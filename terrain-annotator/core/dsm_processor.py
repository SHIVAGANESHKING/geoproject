from qgis.core import QgsRasterLayer, QgsProject, QgsRectangle
from qgis.gui import QgsMapCanvas

class DSMProcessor:
    """Handles DSM raster operations."""
    def __init__(self, canvas: QgsMapCanvas):
        """
        Initializer.

        :param canvas: The QGIS map canvas to add layers to.
        """
        self.canvas = canvas
        self.project = QgsProject.instance()

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

        # Add the layer to the project
        self.project.addMapLayer(raster_layer)

        # Optionally, set the canvas extent to the new layer
        self.canvas.setExtent(raster_layer.extent())

        # Refresh the canvas to show the new layer
        self.canvas.refresh()

        print(f"DSM layer '{file_path}' loaded successfully.")
        return raster_layer