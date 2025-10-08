"""
Enhanced map tools for the Terrain Annotator application.
Includes Pan, Zoom In/Out, Zoom to Extent, and Identify tools.
"""
from qgis.core import QgsVectorLayer, QgsRectangle
from qgis.gui import QgsMapTool, QgsMapToolPan, QgsMapToolZoom, QgsMapToolIdentifyFeature
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QCursor, QPixmap


class PanTool(QgsMapToolPan):
    """Hand tool for panning/scrolling the map."""
    
    def __init__(self, canvas):
        """Initialize the pan tool."""
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(Qt.OpenHandCursor)
        self.dragging = False
    
    def canvasPressEvent(self, event):
        """Change cursor when dragging starts."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.setCursor(Qt.ClosedHandCursor)
        super().canvasPressEvent(event)
    
    def canvasReleaseEvent(self, event):
        """Reset cursor when dragging ends."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.OpenHandCursor)
        super().canvasReleaseEvent(event)


class ZoomInTool(QgsMapToolZoom):
    """Tool for zooming in on the map."""
    
    def __init__(self, canvas):
        """Initialize the zoom in tool."""
        super().__init__(canvas, False)  # False = zoom in
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)


class ZoomOutTool(QgsMapToolZoom):
    """Tool for zooming out on the map."""
    
    def __init__(self, canvas):
        """Initialize the zoom out tool."""
        super().__init__(canvas, True)  # True = zoom out
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)


class IdentifyTool(QgsMapToolIdentifyFeature):
    """Tool for identifying and inspecting features on the map."""
    
    featureIdentified = pyqtSignal(dict)  # Emits feature information
    
    def __init__(self, canvas, layers=None):
        """
        Initialize the identify tool.
        
        :param canvas: The QGIS map canvas
        :param layers: List of layers to identify features from (None = all layers)
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.layers = layers or []
        self.setCursor(Qt.WhatsThisCursor)
    
    def canvasReleaseEvent(self, event):
        """Identify features at click position."""
        if event.button() != Qt.LeftButton:
            return
        
        # Get all layers if none specified
        layers_to_identify = self.layers if self.layers else self.canvas.layers()
        
        # Identify features at click position
        results = self.identify(event.x(), event.y(), layers_to_identify, self.TopDownAll)
        
        if results:
            feature_info = []
            for result in results:
                feature = result.mFeature
                layer = result.mLayer
                
                info = {
                    'layer_name': layer.name(),
                    'feature_id': feature.id(),
                    'attributes': {}
                }
                
                # Get all attributes
                for field in feature.fields():
                    field_name = field.name()
                    field_value = feature[field_name]
                    info['attributes'][field_name] = field_value
                
                feature_info.append(info)
            
            # Emit the first feature's info
            if feature_info:
                self.featureIdentified.emit(feature_info[0])
    
    def set_layers(self, layers):
        """Update the layers to identify from."""
        self.layers = layers


class MeasureTool(QgsMapTool):
    """Tool for measuring distances and areas on the map."""
    
    measurementComplete = pyqtSignal(float, str)  # value, unit
    
    def __init__(self, canvas, measure_type='distance'):
        """
        Initialize the measure tool.
        
        :param canvas: The QGIS map canvas
        :param measure_type: 'distance' or 'area'
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.measure_type = measure_type
        self.points = []
        self.setCursor(Qt.CrossCursor)
        
        from qgis.gui import QgsRubberBand
        from qgis.core import QgsWkbTypes
        from PyQt5.QtGui import QColor
        
        # Create rubber band for visual feedback
        geom_type = QgsWkbTypes.LineGeometry if measure_type == 'distance' else QgsWkbTypes.PolygonGeometry
        self.rubber_band = QgsRubberBand(canvas, geom_type)
        self.rubber_band.setColor(QColor(255, 0, 255, 128))
        self.rubber_band.setWidth(2)
    
    def canvasPressEvent(self, event):
        """Add point on left click, finish on right click."""
        point = self.toMapCoordinates(event.pos())
        
        if event.button() == Qt.LeftButton:
            self.points.append(point)
            self.rubber_band.addPoint(point)
        elif event.button() == Qt.RightButton:
            if len(self.points) > 1:
                self.calculate_measurement()
            self.reset()
    
    def canvasMoveEvent(self, event):
        """Update rubber band as mouse moves."""
        if self.points:
            point = self.toMapCoordinates(event.pos())
            self.rubber_band.reset(self.rubber_band.geometryType())
            for p in self.points:
                self.rubber_band.addPoint(p, False)
            self.rubber_band.addPoint(point, True)
    
    def calculate_measurement(self):
        """Calculate distance or area from points."""
        from qgis.core import QgsDistanceArea, QgsProject
        
        distance_area = QgsDistanceArea()
        distance_area.setSourceCrs(self.canvas.mapSettings().destinationCrs(), QgsProject.instance().transformContext())
        distance_area.setEllipsoid(QgsProject.instance().ellipsoid())
        
        if self.measure_type == 'distance':
            total_distance = 0
            for i in range(len(self.points) - 1):
                total_distance += distance_area.measureLine(self.points[i], self.points[i + 1])
            
            # Convert to kilometers
            distance_km = total_distance / 1000.0
            self.measurementComplete.emit(distance_km, 'km')
        else:  # area
            from qgis.core import QgsGeometry, QgsPolygon, QgsLineString, QgsPoint
            
            # Create polygon from points
            line_string = QgsLineString([QgsPoint(p.x(), p.y()) for p in self.points])
            polygon = QgsPolygon()
            polygon.setExteriorRing(line_string)
            geometry = QgsGeometry(polygon)
            
            area = distance_area.measureArea(geometry)
            area_km2 = area / 1e6  # Convert to km²
            self.measurementComplete.emit(area_km2, 'km²')
    
    def reset(self):
        """Reset the tool."""
        self.points = []
        self.rubber_band.reset()
    
    def deactivate(self):
        """Deactivate the tool."""
        super().deactivate()
        self.reset()


class ZoomToExtentTool:
    """Tool for zooming to full extent or layer extent."""
    
    def __init__(self, canvas):
        """Initialize the zoom to extent tool."""
        self.canvas = canvas
    
    def zoom_to_full_extent(self):
        """Zoom to the full extent of all layers."""
        self.canvas.zoomToFullExtent()
        self.canvas.refresh()
    
    def zoom_to_layer(self, layer):
        """Zoom to the extent of a specific layer."""
        if layer and layer.isValid():
            self.canvas.setExtent(layer.extent())
            self.canvas.refresh()
    
    def zoom_to_selected(self, layer):
        """Zoom to selected features in a layer."""
        if layer and layer.selectedFeatureCount() > 0:
            bbox = layer.boundingBoxOfSelected()
            # Add 10% buffer around selection
            bbox.scale(1.1)
            self.canvas.setExtent(bbox)
            self.canvas.refresh()
