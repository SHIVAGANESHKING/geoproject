import os
import argparse
import psycopg2
import numpy as np
from osgeo import gdal, osr, ogr
from tqdm import tqdm
import tempfile

# --- Configuration ---
PROCESSED_DATA_DIR = "data/processed"
TILE_SIZE = 256

def connect_to_db(db_params):
    """Connects to the PostGIS database and returns the connection."""
    try:
        conn = psycopg2.connect(**db_params)
        print("Database connection established successfully.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database. {e}")
        return None

def fetch_annotations(conn):
    """Fetches all annotations from the database."""
    sql = "SELECT id, ST_AsText(geom), class_id FROM terrain_annotations"
    annotations = []
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                annotations.append({"id": row[0], "geom_wkt": row[1], "class_id": row[2]})
        print(f"Fetched {len(annotations)} annotations from the database.")
    except Exception as e:
        print(f"Error fetching annotations: {e}")
    return annotations

def find_dsm_for_geom(geom_wkt: str, dsm_dir: str) -> str | None:
    """Finds the correct DSM tile for a given geometry WKT."""
    geom = ogr.CreateGeometryFromWkt(geom_wkt)
    if geom is None: return None
    env = geom.GetEnvelope()
    for filename in os.listdir(dsm_dir):
        if filename.endswith(".tif"):
            filepath = os.path.join(dsm_dir, filename)
            ds = gdal.Open(filepath)
            if ds is None: continue
            gt = ds.GetGeoTransform()
            min_x, max_y = gt[0], gt[3]
            max_x, min_y = min_x + gt[1] * ds.RasterXSize, max_y + gt[5] * ds.RasterYSize
            if (env[0] < max_x and env[1] > min_x and env[2] < max_y and env[3] > min_y):
                return filepath
    return None

def calculate_derivatives(dsm_path: str, temp_dir: str):
    """Calculates slope and aspect from a DSM, returning file paths."""
    slope_path = os.path.join(temp_dir, "slope.tif")
    aspect_path = os.path.join(temp_dir, "aspect.tif")
    gdal.DEMProcessing(slope_path, dsm_path, 'slope', options='-p')
    gdal.DEMProcessing(aspect_path, dsm_path, 'aspect')
    return slope_path, aspect_path

def stack_bands(elevation_path, slope_path, aspect_path, temp_dir):
    """Stacks elevation, slope, and aspect into a 3-band virtual raster (VRT)."""
    vrt_path = os.path.join(temp_dir, "stacked.vrt")
    gdal.BuildVRT(vrt_path, [elevation_path, slope_path, aspect_path], separate=True)
    return vrt_path

def clip_and_create_mask(stacked_vrt_path, geom_wkt, class_id, temp_dir):
    """Clips the raster to the geometry and creates a corresponding mask."""
    clipped_raster_path = os.path.join(temp_dir, "clipped_raster.tif")
    mask_path = os.path.join(temp_dir, "mask.tif")

    # Use gdal.Warp to clip the raster to the geometry's extent
    warp_options = gdal.WarpOptions(
        cutlineDSName=geom_wkt,
        cropToCutline=True,
        dstNodata=0  # Set nodata value for areas outside the polygon
    )
    gdal.Warp(clipped_raster_path, stacked_vrt_path, options=warp_options)

    # Create the mask: open the clipped raster to get its dimensions
    src_ds = gdal.Open(clipped_raster_path)
    gt, proj = src_ds.GetGeoTransform(), src_ds.GetProjection()
    cols, rows = src_ds.RasterXSize, src_ds.RasterYSize

    # Create an in-memory mask raster
    mem_driver = gdal.GetDriverByName('MEM')
    mask_ds = mem_driver.Create('', cols, rows, 1, gdal.GDT_Byte)
    mask_ds.SetGeoTransform(gt)
    mask_ds.SetProjection(proj)
    mask_band = mask_ds.GetRasterBand(1)
    mask_band.Fill(0)  # Fill with background value
    mask_band.SetNoDataValue(0)

    # Rasterize the geometry onto the mask with the class_id
    geom = ogr.CreateGeometryFromWkt(geom_wkt)
    gdal.RasterizeLayer(mask_ds, [1], geom.GetLayer(), burn_values=[class_id])

    # Write the in-memory mask to a file
    gdal.GetDriverByName('GTiff').CreateCopy(mask_path, mask_ds)

    return clipped_raster_path, mask_path

def tile_and_save(raster_path, mask_path, ann_id, output_dir):
    """Tiles the clipped raster and mask and saves them as numpy arrays."""
    raster_ds = gdal.Open(raster_path)
    mask_ds = gdal.Open(mask_path)

    for y in range(0, raster_ds.RasterYSize, TILE_SIZE):
        for x in range(0, raster_ds.RasterXSize, TILE_SIZE):
            # Ensure we don't go past the raster edge
            x_size = min(TILE_SIZE, raster_ds.RasterXSize - x)
            y_size = min(TILE_SIZE, raster_ds.RasterYSize - y)

            img_tile = raster_ds.ReadAsArray(x, y, x_size, y_size)
            mask_tile = mask_ds.ReadAsArray(x, y, x_size, y_size)

            # Pad tiles that are smaller than TILE_SIZE
            if img_tile.shape[1] < TILE_SIZE or img_tile.shape[2] < TILE_SIZE:
                pad_y = TILE_SIZE - img_tile.shape[1]
                pad_x = TILE_SIZE - img_tile.shape[2]
                img_tile = np.pad(img_tile, ((0, 0), (0, pad_y), (0, pad_x)), 'constant', constant_values=0)
                mask_tile = np.pad(mask_tile, ((0, pad_y), (0, pad_x)), 'constant', constant_values=0)

            # Save the tiles as numpy arrays
            img_filename = os.path.join(output_dir, f"image_{ann_id}_{x}_{y}.npy")
            mask_filename = os.path.join(output_dir, f"mask_{ann_id}_{x}_{y}.npy")
            np.save(img_filename, img_tile)
            np.save(mask_filename, mask_tile)

def process_annotation(annotation, dsm_dir, output_dir):
    """Full processing pipeline for a single annotation."""
    dsm_path = find_dsm_for_geom(annotation["geom_wkt"], dsm_dir)
    if not dsm_path:
        print(f"  - Could not find DSM for annotation {annotation['id']}. Skipping.")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        slope_path, aspect_path = calculate_derivatives(dsm_path, temp_dir)
        stacked_vrt_path = stack_bands(dsm_path, slope_path, aspect_path, temp_dir)
        clipped_raster_path, mask_path = clip_and_create_mask(
            stacked_vrt_path, annotation["geom_wkt"], annotation["class_id"], temp_dir
        )
        tile_and_save(clipped_raster_path, mask_path, annotation['id'], output_dir)

def main(args):
    """Main function to run the preprocessing pipeline."""
    db_params = {"host": args.db_host, "port": args.db_port, "dbname": args.db_name, "user": args.db_user, "password": args.db_password}
    dsm_dir = args.dsm_dir
    if not os.path.isdir(dsm_dir):
        print(f"Error: DSM directory not found at '{dsm_dir}'. Please provide a valid path.")
        return

    conn = connect_to_db(db_params)
    if not conn: return
    annotations = fetch_annotations(conn)
    conn.close()
    if not annotations: return

    # Create subdirectories for images and masks
    image_dir = os.path.join(PROCESSED_DATA_DIR, "images")
    mask_dir = os.path.join(PROCESSED_DATA_DIR, "masks")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)

    for annotation in tqdm(annotations, desc="Processing Annotations"):
        process_annotation(annotation, dsm_dir, PROCESSED_DATA_DIR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess terrain annotation data for model training.")
    parser.add_argument("--db_host", default="localhost", help="Database host")
    parser.add_argument("--db_port", default="5432", help="Database port")
    parser.add_argument("--db_name", required=True, help="Database name")
    parser.add_argument("--db_user", required=True, help="Database user")
    parser.add_argument("--db_password", required=True, help="Database password")
    parser.add_argument("--dsm_dir", required=True, help="Path to the directory containing raw JAXA DSM tiles.")

    args = parser.parse_args()
    main(args)