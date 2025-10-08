from qgis.core import QgsVectorLayer, QgsFeature, QgsProject, QgsGeometry
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QDialog, QDockWidget
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt, QThreadPool
from .map_canvas import MapCanvas
from .sidebar_widget import SidebarWidget
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.export_dialog import ExportDialog
from .dialogs.class_manager_dialog import ClassManagerDialog
from .terrain_viewer_3d import TerrainViewer3D
from core.dsm_processor import DSMProcessor
from core.database_manager import DatabaseManager
from core.annotation_manager import AnnotationManager
from core.class_manager import ClassManager
from core.statistics import StatisticsCalculator
from models.annotation import Annotation
from utils.exporters import GeoJsonExporter
from utils.threads import Worker
from tools.polygon_tool import PolygonTool
from tools.select_tool import SelectTool
from tools.edit_tool import EditTool

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

        # Sidebar
        self.sidebar = SidebarWidget()

        # Map Canvas
        self.map_canvas = MapCanvas()

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.map_canvas, 1)

        self.statusBar().showMessage("Ready")

        # Initialize core components
        self.db_manager = DatabaseManager()
        self.annotation_manager = AnnotationManager(self.db_manager)
        self.class_manager = ClassManager(self.db_manager)
        self.dsm_processor = DSMProcessor(self.map_canvas)
        self.stats_calculator = StatisticsCalculator()
        self.last_drawn_geometry = None
        self.last_calculated_stats = {}
        self.selected_feature_id = None
        self.loaded_annotations_layer = None
        self.threadpool = QThreadPool()
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        # Setup menu bar
        self._create_menu_bar()

        # Setup tools
        self.polygon_tool = PolygonTool(self.map_canvas)
        self.polygon_tool.polygonCreated.connect(self.handle_polygon_created)
        self.select_tool = None
        self.edit_tool = None

        # Connect sidebar signals
        self.sidebar.start_draw_button.clicked.connect(self.activate_drawing_tool)
        self.sidebar.edit_button.clicked.connect(self.toggle_edit_mode)
        self.sidebar.delete_button.clicked.connect(self.delete_selected_annotation)
        self.sidebar.save_button.clicked.connect(self.save_annotation)
        self.sidebar.export_button.clicked.connect(self.export_annotations)

        # Setup temporary layer for annotations
        self._setup_annotation_layer()

        # Initial population of sidebar classes
        self.sidebar.populate_classes(self.class_manager.get_all_classes())

        # Setup the 3D viewer dock
        self._create_3d_viewer_dock()

        # Connect the 3D viewer button
        self.sidebar.view_3d_button.clicked.connect(self.show_3d_viewer)

    def _create_3d_viewer_dock(self):
        """Creates the dock widget for the 3D viewer."""
        self.viewer_3d_dock = QDockWidget("3D Terrain Viewer", self)
        self.viewer_3d = TerrainViewer3D(self)
        self.viewer_3d_dock.setWidget(self.viewer_3d)
        self.viewer_3d_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.viewer_3d_dock)
        self.viewer_3d_dock.setVisible(False)  # Start hidden

    def show_3d_viewer(self):
        """Shows the 3D viewer dock."""
        # TODO: This would eventually pass the selected geometry to the viewer
        self.viewer_3d_dock.setVisible(True)
        self.statusBar().showMessage("3D viewer opened (placeholder).", 3000)

    def _setup_annotation_layer(self):
        """Creates a temporary memory layer to display drawn polygons."""
        self.annotation_layer = QgsVectorLayer("Polygon?crs=epsg:4326", "Annotations", "memory")
        QgsProject.instance().addMapLayer(self.annotation_layer)

    def activate_drawing_tool(self):
        """Activates the polygon drawing tool."""
        self.map_canvas.setMapTool(self.polygon_tool)
        self.statusBar().showMessage("Drawing mode activated. Left-click to add points, right-click to finish.")

    def handle_polygon_created(self, geometry):
        """Handles the new polygon by adding it to the temporary layer and calculating stats."""
        self.last_drawn_geometry = geometry

        # Add feature to temp layer
        feature = QgsFeature()
        feature.setGeometry(geometry)
        provider = self.annotation_layer.dataProvider()
        provider.truncate()
        provider.addFeature(feature)
        self.annotation_layer.updateExtents()
        self.map_canvas.refresh()

        # Calculate and display stats
        self.update_statistics(geometry)

        self.statusBar().showMessage("Polygon created. Statistics updated.", 5000)

    def update_statistics(self, geometry):
        """
        Calculates statistics for a geometry.
        Geometry stats are done in the main thread; raster stats are offloaded.
        """
        # Geometry stats are fast, can be done in the main thread
        geom_stats = self.stats_calculator.calculate_geometry_stats(geometry)
        self.sidebar.area_label.setText(f"{geom_stats['area'] / 1e6:.4f} km²")
        self.sidebar.perimeter_label.setText(f"{geom_stats['perimeter'] / 1e3:.2f} km")
        self.last_calculated_stats = geom_stats  # Store partial stats immediately

        # Raster stats are slow, run them in a background thread
        dsm_layer = self.dsm_processor.current_dsm_layer
        if dsm_layer:
            self.statusBar().showMessage("Calculating raster statistics...", 0)  # Persistent message
            worker = Worker(self.stats_calculator.calculate_raster_stats, geometry, dsm_layer)
            worker.signals.result.connect(self.handle_raster_stats_result)
            worker.signals.finished.connect(lambda: self.statusBar().showMessage("Statistics updated.", 5000))
            worker.signals.error.connect(lambda err: self.statusBar().showMessage(f"Error calculating stats: {err}", 5000))
            self.threadpool.start(worker)
        else:
            self.sidebar.mean_elevation_label.setText("No DSM loaded")
            self.sidebar.mean_slope_label.setText("N/A")

    def handle_raster_stats_result(self, raster_stats):
        """
        Handles the result from the background statistics calculation.
        This method is executed in the main thread.
        """
        if raster_stats:
            self.sidebar.mean_elevation_label.setText(f"{raster_stats['elevation_mean']:.2f} m")
            slope = raster_stats.get('slope_mean')
            self.sidebar.mean_slope_label.setText(f"{slope:.2f}°" if slope is not None else "N/A")
            # Merge raster stats with existing geometry stats
            self.last_calculated_stats.update(raster_stats)
        else:
            self.sidebar.mean_elevation_label.setText("N/A")
            self.sidebar.mean_slope_label.setText("N/A")

    def save_annotation(self):
        """Saves the last drawn polygon to the database."""
        if self.last_drawn_geometry is None:
            self.statusBar().showMessage("No polygon drawn to save.", 5000)
            return

        selected_class = next((name for name, radio in self.sidebar.class_radios.items() if radio.isChecked()), None)

        if not selected_class:
            self.statusBar().showMessage("Please select a terrain class.", 5000)
            return

        # Create Annotation object with calculated stats
        new_annotation = Annotation(
            geom=self.last_drawn_geometry.asWkt(),
            class_name=selected_class,
            class_id=list(self.sidebar.class_radios.keys()).index(selected_class) + 1,
            area_sqm=self.last_calculated_stats.get('area', 0.0),
            perimeter_m=self.last_calculated_stats.get('perimeter', 0.0),
            elevation_min=self.last_calculated_stats.get('elevation_min'),
            elevation_max=self.last_calculated_stats.get('elevation_max'),
            elevation_mean=self.last_calculated_stats.get('elevation_mean'),
            slope_mean=self.last_calculated_stats.get('slope_mean')
        )

        if self.annotation_manager.save_annotation(new_annotation):
            self.statusBar().showMessage(f"Annotation saved as '{selected_class}'.", 5000)
            self.last_drawn_geometry = None
            self.last_calculated_stats = {}
            self.annotation_layer.dataProvider().truncate()
            self.map_canvas.refresh()
        else:
            self.statusBar().showMessage("Failed to save annotation.", 5000)

    def _create_menu_bar(self):
        """Creates the main menu bar."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        load_dsm_action = QAction("Load DSM...", self)
        load_dsm_action.triggered.connect(self.load_dsm)
        file_menu.addAction(load_dsm_action)
        load_ann_action = QAction("Load Annotations from DB", self)
        load_ann_action.triggered.connect(self.load_annotations)
        file_menu.addAction(load_ann_action)
        file_menu.addSeparator()
        manage_classes_action = QAction("Manage Classes...", self)
        manage_classes_action.triggered.connect(self.open_class_manager)
        file_menu.addAction(manage_classes_action)
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        undo_stack = QgsProject.instance().undoStack()
        undo_action = undo_stack.createUndoAction(self, "&Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        redo_action = undo_stack.createRedoAction(self, "&Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

    def open_settings_dialog(self):
        """Opens the application settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def open_class_manager(self):
        """Opens the dialog to manage terrain classes."""
        if not self.db_manager.is_connected():
            self.db_manager.connect() # Attempt to connect
            if not self.db_manager.is_connected():
                return # Error message is shown by the manager

        dialog = ClassManagerDialog(self.class_manager, self)
        dialog.exec()
        # After closing the dialog, refresh the classes in the sidebar
        self.sidebar.populate_classes(self.class_manager.get_all_classes())

    def load_annotations(self):
        """Loads annotations from the database and displays them on the map."""
        annotations = self.annotation_manager.get_all_annotations()
        if not annotations:
            self.statusBar().showMessage("No annotations found in the database.", 5000)
            return

        uri = "Polygon?crs=epsg:4326&field=id:integer&field=class_name:string"
        self.loaded_annotations_layer = QgsVectorLayer(uri, "Loaded Annotations", "memory")
        provider = self.loaded_annotations_layer.dataProvider()

        features = []
        for ann in annotations:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromWkt(ann.geom))
            feature.setId(ann.id)
            feature.setAttributes([ann.id, ann.class_name])
            features.append(feature)

        provider.addFeatures(features)
        QgsProject.instance().addMapLayer(self.loaded_annotations_layer)

        # Setup tools for the new layer
        self.select_tool = SelectTool(self.map_canvas, self.loaded_annotations_layer)
        self.select_tool.featureSelected.connect(self.handle_feature_selected)
        self.edit_tool = EditTool(self.map_canvas, self.loaded_annotations_layer)

        self.map_canvas.refresh()
        self.statusBar().showMessage(f"Loaded {len(features)} annotations. Edit and Select tools are now available.", 5000)

    def toggle_edit_mode(self):
        """Toggles the vertex editing mode for the loaded annotations layer."""
        if not self.edit_tool:
            self.statusBar().showMessage("Load annotations to enable editing.", 5000)
            return

        if self.edit_tool.is_active():
            # Stop editing
            self.update_edited_features()
            self.edit_tool.deactivate()
            self.sidebar.edit_button.setText("Edit Annotation")
            self.statusBar().showMessage("Editing stopped.", 3000)
        else:
            # Start editing
            self.edit_tool.activate()
            self.sidebar.edit_button.setText("Stop Editing")
            self.statusBar().showMessage("Editing mode activated. Select a vertex to move it.", 5000)

    def update_edited_features(self):
        """Finds modified features, recalculates stats, and saves them to the DB."""
        if not self.loaded_annotations_layer or not self.loaded_annotations_layer.isEditable():
            return

        modified_features = self.loaded_annotations_layer.editBuffer()
        if not modified_features:
            return

        for feature_id, feature in modified_features.changedGeometries().items():
            # Recalculate stats
            self.update_statistics(feature.geometry())

            # Create annotation object and save
            updated_annotation = Annotation(
                id=feature_id,
                geom=feature.geometry().asWkt(),
                class_name=feature['class_name'], # Get class name from feature attribute
                area_sqm=self.last_calculated_stats.get('area', 0.0),
                perimeter_m=self.last_calculated_stats.get('perimeter', 0.0),
                elevation_min=self.last_calculated_stats.get('elevation_min'),
                elevation_max=self.last_calculated_stats.get('elevation_max'),
                elevation_mean=self.last_calculated_stats.get('elevation_mean'),
                slope_mean=self.last_calculated_stats.get('slope_mean')
            )
            self.annotation_manager.update_annotation(updated_annotation)

    def handle_feature_selected(self, feature_id):
        """Stores the ID of the selected feature."""
        self.selected_feature_id = feature_id
        self.statusBar().showMessage(f"Feature {feature_id} selected.", 3000)

    def delete_selected_annotation(self):
        """Deletes the currently selected annotation."""
        if self.selected_feature_id is None:
            self.statusBar().showMessage("No feature selected to delete.", 5000)
            return

        # Use the undo stack to make the deletion undoable
        undo_stack = QgsProject.instance().undoStack()
        undo_stack.beginCommand(f"Delete feature {self.selected_feature_id}")

        if self.annotation_manager.delete_annotation(self.selected_feature_id):
            self.loaded_annotations_layer.dataProvider().deleteFeatures([self.selected_feature_id])
            self.map_canvas.refresh()
            self.statusBar().showMessage(f"Feature {self.selected_feature_id} deleted.", 5000)
            self.selected_feature_id = None
            undo_stack.endCommand()
        else:
            self.statusBar().showMessage("Failed to delete annotation from database.", 5000)
            undo_stack.undo() # Rollback the command

    def export_annotations(self):
        """Exports all annotations to a GeoJSON file."""
        confirm_dialog = ExportDialog(self)
        if confirm_dialog.exec() == QDialog.DialogCode.Accepted:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Annotations", "", "GeoJSON Files (*.geojson)"
            )
            if file_path:
                annotations = self.annotation_manager.get_all_annotations()
                if annotations:
                    if GeoJsonExporter.export_annotations(annotations, file_path):
                        self.statusBar().showMessage(f"Successfully exported to {file_path}", 5000)
                    else:
                        self.statusBar().showMessage("Export failed.", 5000)
                else:
                    self.statusBar().showMessage("No annotations to export.", 5000)

    def load_dsm(self):
        """Opens a file dialog to load a DSM layer."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load DSM", "", "GeoTIFF Files (*.tif *.tiff)"
        )
        if file_path:
            self.dsm_processor.load_dsm_layer(file_path)