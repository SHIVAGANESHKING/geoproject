from qgis.core import (
    QgsWkbTypes, QgsPointXY, QgsPolygon, QgsFeature, 
    QgsGeometry, QgsLineString, QgsPoint
)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox


def is_polygon_simple(geometry):
    """
    Checks if a polygon is simple (doesn't self-intersect).
    
    :param geometry: QgsGeometry object
    :return: True if simple, False otherwise
    """
    if not geometry or geometry.isEmpty():
        return False
    
    # Use QGIS built-in validation
    return geometry.isGeosValid()


class PolygonTool(QgsMapToolEmitPoint):
    """A map tool for drawing a polygon by clicking points."""

    # Signal emitted when a polygon is created
    polygonCreated = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        """Initializer."""
        super().__init__(canvas)
        self.canvas = canvas
        self.points = []

        # A rubber band for visualizing the polygon being drawn
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 128))  # Semi-transparent red
        self.rubber_band.setWidth(2)

    def canvasPressEvent(self, event):
        """Handles a mouse press event (left or right-click)."""
        # Left-click adds a vertex
        if event.button() == 1:  # Left button
            point = self.toMapCoordinates(event.pos())
            self.points.append(point)
            self.update_rubber_band()
        # Right-click finishes the polygon
        elif event.button() == 2:  # Right button
            if len(self.points) > 2:
                self.finalize_polygon()
            else:
                self.reset()  # Not enough points, so reset

    def canvasMoveEvent(self, event):
        """Handles mouse move event to update the rubber band."""
        if self.points:
            current_point = self.toMapCoordinates(event.pos())
            self.update_rubber_band(current_point)

    def update_rubber_band(self, temporary_point=None):
        """Updates the rubber band with the current list of points."""
        points_for_rubber_band = self.points[:]
        if temporary_point:
            points_for_rubber_band.append(temporary_point)

        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        for point in points_for_rubber_band:
            self.rubber_band.addPoint(point, False)

        if len(points_for_rubber_band) > 2:
            # Close the loop for visualization
            self.rubber_band.addPoint(points_for_rubber_band[0], True)

        self.rubber_band.show()

    def finalize_polygon(self):
        """Finalizes the polygon, validates it, and emits the `polygonCreated` signal."""
        if len(self.points) > 2:
            # Create a QgsLineString from the points for QGIS 3.x
            line_string = QgsLineString([QgsPoint(p.x(), p.y()) for p in self.points])
            
            # Create polygon and set the exterior ring
            polygon = QgsPolygon()
            polygon.setExteriorRing(line_string)
            
            # Create geometry from polygon
            geometry = QgsGeometry(polygon)

            # Validate that the polygon is simple (doesn't self-intersect)
            if not is_polygon_simple(geometry):
                QMessageBox.warning(
                    None, "Invalid Geometry", 
                    "The drawn polygon cannot intersect itself. Please try again."
                )
                self.reset()
                return

            # Emit the signal with the created geometry
            self.polygonCreated.emit(geometry)
        
        self.reset()

    def reset(self):
        """Resets the tool, clearing points and hiding the rubber band."""
        self.points = []
        self.rubber_band.reset()

    def deactivate(self):
        """Called when the tool is deactivated."""
        super().deactivate()
        self.rubber_band.reset()

    def activate(self):
        """Called when the tool is activated."""
        super().activate()
        self.points = []
        self.rubber_band.reset()
