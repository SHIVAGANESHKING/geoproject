from qgis.core import QgsRasterLayer, QgsProject, QgsRectangle, QgsGeometry
from qgis.gui import QgsMapCanvas
from osgeo import gdal
import tempfile
import os

class DSMProcessor:
    """Handles DSM raster operations."""
    def __init__(self, canvas: QgsMapCanvas):
        """
        Initializer.

        :param canvas: The QGIS map canvas to add layers to.
        """
        self.canvas = canvas
        self.project = QgsProject.instance()
        self.current_dsm_layer = None

    def load_dsm_layer(self, file_path: str) -> QgsRasterLayer | None:
        """
        Loads a DSM from a file and adds it to the map.

        :param file_path: Path to the DSM GeoTIFF file.
        :return: The loaded QgsRasterLayer or None if loading failed.
        """
        layer_name = "DSM"
        raster_layer = QgsRasterLayer(file_path, layer_name)

        if not raster_layer.isValid():
            print(f"Error: Failed to load DSM layer from {file_path}")
            return None

        # Add the layer to the project and store it
        self.project.addMapLayer(raster_layer)
        self.current_dsm_layer = raster_layer

        # Optionally, set the canvas extent to the new layer
        self.canvas.setExtent(raster_layer.extent())

        # The main window is now responsible for refreshing the layer set
        # self.canvas.refresh()

        print(f"DSM layer '{file_path}' loaded successfully.")
        return raster_layer

    def clip_dsm_by_geometry(self, geometry: QgsGeometry) -> str | None:
        """
        Clips the current DSM raster to the extent of a given geometry.

        :param geometry: The QgsGeometry to clip the raster to.
        :return: The file path to the temporary clipped raster, or None on failure.
        """
        if not self.current_dsm_layer:
            print("Error: No DSM layer loaded to clip.")
            return None

        # Get the bounding box of the geometry in the layer's CRS
        source_crs = geometry.crs()
        layer_crs = self.current_dsm_layer.crs()
        if source_crs != layer_crs:
            from qgis.core import QgsCoordinateTransform
            transform = QgsCoordinateTransform(source_crs, layer_crs, QgsProject.instance())
            geometry.transform(transform)

        bbox = geometry.boundingBox()
        output_bounds = (bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum())

        # Create a temporary file for the clipped output
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "clipped_dsm.tif")

        # Use GDAL Warp to clip the raster
        try:
            gdal.Warp(
                temp_path,
                self.current_dsm_layer.source(),
                outputBounds=output_bounds,
                format='GTiff'
            )
            print(f"Clipped DSM saved to temporary file: {temp_path}")
            return temp_path
        except Exception as e:
            print(f"Error clipping DSM: {e}")
            return None