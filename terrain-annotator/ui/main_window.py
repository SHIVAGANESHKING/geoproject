from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog
from PyQt6.QtGui import QAction
from .map_canvas import MapCanvas
from core.dsm_processor import DSMProcessor

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Terrain Annotator")
        self.resize(1200, 800)

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar (placeholder)
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(self.sidebar)
        # TODO: Add sidebar widgets here

        # Map Canvas
        self.map_canvas = MapCanvas()

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.map_canvas, 1)

        self.statusBar().showMessage("Ready")

        # Initialize core components
        self.dsm_processor = DSMProcessor(self.map_canvas)

        # Setup menu bar
        self._create_menu_bar()

    def _create_menu_bar(self):
        """Creates the main menu bar."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        load_dsm_action = QAction("Load DSM...", self)
        load_dsm_action.triggered.connect(self.load_dsm)
        file_menu.addAction(load_dsm_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def load_dsm(self):
        """Opens a file dialog to load a DSM layer."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load DSM", "", "GeoTIFF Files (*.tif *.tiff)"
        )
        if file_path:
            self.dsm_processor.load_dsm_layer(file_path)