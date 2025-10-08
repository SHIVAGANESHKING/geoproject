import os
import argparse
import numpy as np
import tensorflow as tf
from osgeo import gdal
from tqdm import tqdm
from model import build_fcn_resnet
from preprocess import calculate_derivatives, stack_bands, TILE_SIZE

# --- Configuration ---
MODELS_DIR = "models"
OUTPUT_DIR = "output"
INPUT_SHAPE = (256, 256, 3)
NUM_CLASSES = 7

def predict_on_tile(model, tile):
    """Runs prediction on a single tile and returns the predicted class mask."""
    # Add a batch dimension and predict
    prediction = model.predict(np.expand_dims(tile, axis=0))
    # Get the class with the highest probability for each pixel
    predicted_mask = np.argmax(prediction[0], axis=-1)
    return predicted_mask

def main(args):
    """Main function to run inference on a new DSM tile."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load the trained model
    model_path = os.path.join(MODELS_DIR, "fcn_resnet_best.keras")
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}. Please train the model first.")
        return

    # When loading a model with custom loss functions, you must provide them.
    from train import dice_loss, combined_loss
    custom_objects = {"combined_loss": combined_loss, "dice_loss": dice_loss}
    model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
    print("Trained model loaded successfully.")

    # 2. Preprocess the input DSM
    print("Preprocessing input DSM...")
    with tempfile.TemporaryDirectory() as temp_dir:
        slope_path, aspect_path = calculate_derivatives(args.input_dsm, temp_dir)
        stacked_vrt_path = stack_bands(args.input_dsm, slope_path, aspect_path, temp_dir)

        # 3. Open the stacked raster and prepare for tiling
        src_ds = gdal.Open(stacked_vrt_path)
        gt, proj = src_ds.GetGeoTransform(), src_ds.GetProjection()
        cols, rows = src_ds.RasterXSize, src_ds.RasterYSize

        # Create an output raster for the stitched prediction
        driver = gdal.GetDriverByName('GTiff')
        output_path = os.path.join(OUTPUT_DIR, f"prediction_{os.path.basename(args.input_dsm)}")
        out_ds = driver.Create(output_path, cols, rows, 1, gdal.GDT_Byte)
        out_ds.SetGeoTransform(gt)
        out_ds.SetProjection(proj)
        out_band = out_ds.GetRasterBand(1)

        # 4. Iterate over the raster, predict tile by tile, and write to output
        for y in tqdm(range(0, rows, TILE_SIZE), desc="Predicting Tiles"):
            for x in range(0, cols, TILE_SIZE):
                x_size = min(TILE_SIZE, cols - x)
                y_size = min(TILE_SIZE, rows - y)

                img_tile = src_ds.ReadAsArray(x, y, x_size, y_size)

                # Pad tile if necessary
                if img_tile.shape[1] < TILE_SIZE or img_tile.shape[2] < TILE_SIZE:
                    pad_y = TILE_SIZE - img_tile.shape[1]
                    pad_x = TILE_SIZE - img_tile.shape[2]
                    img_tile = np.pad(img_tile, ((0, 0), (0, pad_y), (0, pad_x)), 'constant')

                # Transpose from (bands, height, width) to (height, width, bands)
                img_tile = img_tile.transpose((1, 2, 0))

                predicted_mask = predict_on_tile(model, img_tile)

                # Write the un-padded portion of the mask to the output raster
                out_band.WriteArray(predicted_mask[:y_size, :x_size], x, y)

    out_ds.FlushCache()
    print(f"\nInference complete. Prediction map saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run inference on a new DSM tile.")
    parser.add_argument("--input_dsm", required=True, help="Path to the input JAXA DSM GeoTIFF file.")

    args = parser.parse_args()
    main(args)