"""
Map toolbar widget with navigation and annotation tools.
"""
from PyQt5.QtWidgets import (
    QToolBar, QAction, QActionGroup, QMessageBox, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal


class MapToolbar(QToolBar):
    """Toolbar for map navigation and annotation tools."""
    
    toolActivated = pyqtSignal(str)  # Emits tool name when activated
    
    def __init__(self, parent=None):
        """Initialize the toolbar."""
        super().__init__("Map Tools", parent)
        self.setMovable(False)
        self.setFloatable(False)
        
        # Create action group for mutually exclusive tools
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        
        self._create_actions()
        self._setup_toolbar()
    
    def _create_actions(self):
        """Create all toolbar actions."""
        # Navigation Tools
        self.pan_action = QAction("Pan", self)
        self.pan_action.setToolTip("Pan/Move the map (Hand tool)")
        self.pan_action.setCheckable(True)
        self.pan_action.setShortcut("H")
        self.pan_action.triggered.connect(lambda: self.toolActivated.emit("pan"))
        self.tool_group.addAction(self.pan_action)
        
        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.setToolTip("Zoom in by dragging a box")
        self.zoom_in_action.setCheckable(True)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(lambda: self.toolActivated.emit("zoom_in"))
        self.tool_group.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.setToolTip("Zoom out by clicking or dragging")
        self.zoom_out_action.setCheckable(True)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(lambda: self.toolActivated.emit("zoom_out"))
        self.tool_group.addAction(self.zoom_out_action)
        
        self.zoom_full_action = QAction("Zoom to Full Extent", self)
        self.zoom_full_action.setToolTip("Zoom to show all layers")
        self.zoom_full_action.setShortcut("Ctrl+Shift+F")
        self.zoom_full_action.triggered.connect(lambda: self.toolActivated.emit("zoom_full"))
        
        self.zoom_layer_action = QAction("Zoom to Layer", self)
        self.zoom_layer_action.setToolTip("Zoom to active layer extent")
        self.zoom_layer_action.setShortcut("Ctrl+Shift+L")
        self.zoom_layer_action.triggered.connect(lambda: self.toolActivated.emit("zoom_layer"))
        
        self.zoom_selected_action = QAction("Zoom to Selection", self)
        self.zoom_selected_action.setToolTip("Zoom to selected features")
        self.zoom_selected_action.setShortcut("Ctrl+Shift+S")
        self.zoom_selected_action.triggered.connect(lambda: self.toolActivated.emit("zoom_selected"))
        
        # Annotation Tools
        self.draw_polygon_action = QAction("Draw Polygon", self)
        self.draw_polygon_action.setToolTip("Draw a new polygon annotation")
        self.draw_polygon_action.setCheckable(True)
        self.draw_polygon_action.setShortcut("D")
        self.draw_polygon_action.triggered.connect(lambda: self.toolActivated.emit("draw_polygon"))
        self.tool_group.addAction(self.draw_polygon_action)
        
        self.select_action = QAction("Select Features", self)
        self.select_action.setToolTip("Select features by clicking")
        self.select_action.setCheckable(True)
        self.select_action.setShortcut("S")
        self.select_action.triggered.connect(lambda: self.toolActivated.emit("select"))
        self.tool_group.addAction(self.select_action)
        
        self.edit_action = QAction("Edit Vertices", self)
        self.edit_action.setToolTip("Edit polygon vertices")
        self.edit_action.setCheckable(True)
        self.edit_action.setShortcut("E")
        self.edit_action.triggered.connect(lambda: self.toolActivated.emit("edit"))
        self.tool_group.addAction(self.edit_action)
        
        # Information Tools
        self.identify_action = QAction("Identify", self)
        self.identify_action.setToolTip("View feature information")
        self.identify_action.setCheckable(True)
        self.identify_action.setShortcut("I")
        self.identify_action.triggered.connect(lambda: self.toolActivated.emit("identify"))
        self.tool_group.addAction(self.identify_action)
        
        self.measure_distance_action = QAction("Measure Distance", self)
        self.measure_distance_action.setToolTip("Measure distance between points")
        self.measure_distance_action.setCheckable(True)
        self.measure_distance_action.setShortcut("M")
        self.measure_distance_action.triggered.connect(lambda: self.toolActivated.emit("measure_distance"))
        self.tool_group.addAction(self.measure_distance_action)
        
        self.measure_area_action = QAction("Measure Area", self)
        self.measure_area_action.setToolTip("Measure area of a polygon")
        self.measure_area_action.setCheckable(True)
        self.measure_area_action.setShortcut("Ctrl+M")
        self.measure_area_action.triggered.connect(lambda: self.toolActivated.emit("measure_area"))
        self.tool_group.addAction(self.measure_area_action)
        
        # Refresh action
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setToolTip("Refresh the map canvas")
        self.refresh_action.setShortcut("F5")
        self.refresh_action.triggered.connect(lambda: self.toolActivated.emit("refresh"))
    
    def _setup_toolbar(self):
        """Setup the toolbar with actions organized in groups."""
        # Navigation section
        self.addWidget(QLabel(" Navigation: "))
        self.addAction(self.pan_action)
        self.addAction(self.zoom_in_action)
        self.addAction(self.zoom_out_action)
        self.addSeparator()
        self.addAction(self.zoom_full_action)
        self.addAction(self.zoom_layer_action)
        self.addAction(self.zoom_selected_action)
        
        self.addSeparator()
        
        # Annotation section
        self.addWidget(QLabel(" Annotation: "))
        self.addAction(self.draw_polygon_action)
        self.addAction(self.select_action)
        self.addAction(self.edit_action)
        
        self.addSeparator()
        
        # Information section
        self.addWidget(QLabel(" Info: "))
        self.addAction(self.identify_action)
        self.addAction(self.measure_distance_action)
        self.addAction(self.measure_area_action)
        
        self.addSeparator()
        self.addAction(self.refresh_action)
        
        # Set pan as default
        self.pan_action.setChecked(True)
    
    def set_tool_enabled(self, tool_name, enabled):
        """Enable or disable a specific tool."""
        tool_actions = {
            'pan': self.pan_action,
            'zoom_in': self.zoom_in_action,
            'zoom_out': self.zoom_out_action,
            'draw_polygon': self.draw_polygon_action,
            'select': self.select_action,
            'edit': self.edit_action,
            'identify': self.identify_action,
            'measure_distance': self.measure_distance_action,
            'measure_area': self.measure_area_action,
        }
        
        if tool_name in tool_actions:
            tool_actions[tool_name].setEnabled(enabled)
    
    def activate_tool(self, tool_name):
        """Programmatically activate a tool."""
        tool_actions = {
            'pan': self.pan_action,
            'zoom_in': self.zoom_in_action,
            'zoom_out': self.zoom_out_action,
            'draw_polygon': self.draw_polygon_action,
            'select': self.select_action,
            'edit': self.edit_action,
            'identify': self.identify_action,
            'measure_distance': self.measure_distance_action,
            'measure_area': self.measure_area_action,
        }
        
        if tool_name in tool_actions:
            tool_actions[tool_name].setChecked(True)
