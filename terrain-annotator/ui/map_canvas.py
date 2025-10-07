import os
import sys
from qgis.core import QgsApplication, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapCanvas
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

def initialize_qgis():
    """
    Initializes the QGIS application.
    Tries to find the QGIS installation path in common locations.
    """
    # Check if QGIS_PREFIX_PATH is set
    qgis_prefix = os.getenv("QGIS_PREFIX_PATH")
    if qgis_prefix:
        QgsApplication.setPrefixPath(qgis_prefix, True)
        print(f"Using QGIS_PREFIX_PATH: {qgis_prefix}")
    else:
        # Try common paths for different OS
        paths = []
        if sys.platform == 'darwin':  # macOS
            paths.append('/Applications/QGIS.app/Contents/MacOS')
        elif sys.platform == 'win32':  # Windows
            paths.append('C:\\Program Files\\QGIS 3.28\\apps\\qgis-ltr')
            paths.append('C:\\OSGeo4W\\apps\\qgis-ltr')
        elif sys.platform == 'linux': # Linux
            paths.append('/usr')
            paths.append('/usr/local')

        for path in paths:
            if os.path.exists(os.path.join(path, 'bin', 'qgis_core.dll' if sys.platform == 'win32' else 'lib/libqgis_core.so.3.28.11')): # A more specific check might be needed
                QgsApplication.setPrefixPath(path, True)
                print(f"Found and set QGIS prefix path: {path}")
                break
        else:
            print("\nWarning: Could not automatically find QGIS installation.")
            print("Please set the 'QGIS_PREFIX_PATH' environment variable to your QGIS installation directory.")

    # Initialize QGIS
    try:
        qgis_app = QgsApplication([], True)
        qgis_app.initQgis()
        print("QGIS Initialized Successfully.")
        return qgis_app
    except Exception as e:
        print(f"Fatal Error: Could not initialize QGIS. Please check your installation and QGIS_PREFIX_PATH. Error: {e}")
        return None

# Initialize QGIS application singleton
qgis_app = initialize_qgis()


class MapCanvas(QgsMapCanvas):
    """A custom QGIS Map Canvas widget."""
    def __init__(self, parent=None):
        """Initializer."""
        if not qgis_app:
            raise RuntimeError("QGIS Application could not be initialized.")

        super().__init__(parent)
        self.setCanvasColor(QColor("white"))
        self.enableAntiAliasing(True)

        # Set project and CRS
        self.project = QgsProject.instance()
        self.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:3857")) # Web Mercator

        self.load_basemap()

    def load_basemap(self):
        """Loads an OpenStreetMap basemap layer."""
        url = "type=xyz&url=https://a.tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0"
        basemap_layer = QgsRasterLayer(url, "OpenStreetMap", "wms")

        if basemap_layer.isValid():
            self.project.addMapLayer(basemap_layer)
            self.setLayers([basemap_layer])
            # The extent will be set once the layer is loaded, or can be set manually
        else:
            print("Error: Basemap layer failed to load.")

    def __del__(self):
        """Destructor to clean up QGIS resources."""
        # The QgsApplication should be cleaned up at the very end of the application's life.
        # Doing it here can cause crashes. It's better to manage it in main.py.
        pass