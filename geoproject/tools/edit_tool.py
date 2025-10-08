from qgis.gui import QgsMapCanvas, QgsMapToolIdentifyFeature
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class EditTool:
    """
    A wrapper for editing polygon vertices in a vector layer.
    This uses the layer's edit buffer and programmatic vertex manipulation.
    """
    def __init__(self, canvas: QgsMapCanvas, layer: QgsVectorLayer):
        """
        Initializer.

        :param canvas: The QGIS map canvas.
        :param layer: The vector layer to be edited.
        """
        self.canvas = canvas
        self.layer = layer
        self._is_active = False
        self._selected_feature_id = None

        # Store the original map tool to restore later
        self._previous_tool = None

    def activate(self):
        """
        Activates the editing mode for the layer.
        Starts editing if not already in edit mode.
        """
        if not self.layer.isEditable():
            self.layer.startEditing()

        self._is_active = True
        
        # Enable vertex markers for visual feedback
        self.layer.setSelectedFeatures([])
        
        print("Edit mode activated. You can now modify vertices using QGIS's native tools.")
        print("Tip: Use the 'Vertex Tool' from QGIS toolbar for best experience.")

    def deactivate(self, commit_changes=True):
        """
        Deactivates the tool and optionally commits changes.
        
        :param commit_changes: If True, saves changes. If False, discards them.
        """
        if not self._is_active:
            return

        if self.layer.isEditable():
            if commit_changes:
                if not self.layer.commitChanges():
                    print(f"Error committing changes: {self.layer.commitErrors()}")
                else:
                    print("Changes committed successfully.")
            else:
                self.layer.rollBack()
                print("Changes rolled back.")

        self._is_active = False
        self._selected_feature_id = None

    def is_active(self):
        """Checks if the edit tool is currently active."""
        return self._is_active

    def select_feature(self, feature_id: int):
        """
        Selects a feature for editing.
        
        :param feature_id: The ID of the feature to select.
        """
        self._selected_feature_id = feature_id
        self.layer.selectByIds([feature_id])

    def move_vertex(self, feature_id: int, vertex_index: int, new_position: QgsPointXY):
        """
        Moves a vertex of a feature to a new position.
        
        :param feature_id: The feature ID.
        :param vertex_index: The index of the vertex to move.
        :param new_position: The new position as QgsPointXY.
        :return: True if successful, False otherwise.
        """
        if not self.layer.isEditable():
            print("Layer is not in edit mode.")
            return False

        feature = self.layer.getFeature(feature_id)
        if not feature.isValid():
            print(f"Feature {feature_id} not found.")
            return False

        geometry = feature.geometry()
        
        # Move the vertex
        if geometry.moveVertex(new_position.x(), new_position.y(), vertex_index):
            # Update the feature geometry
            self.layer.changeGeometry(feature_id, geometry)
            self.canvas.refresh()
            return True
        else:
            print(f"Failed to move vertex {vertex_index}.")
            return False

    def delete_vertex(self, feature_id: int, vertex_index: int):
        """
        Deletes a vertex from a feature.
        
        :param feature_id: The feature ID.
        :param vertex_index: The index of the vertex to delete.
        :return: True if successful, False otherwise.
        """
        if not self.layer.isEditable():
            print("Layer is not in edit mode.")
            return False

        feature = self.layer.getFeature(feature_id)
        if not feature.isValid():
            print(f"Feature {feature_id} not found.")
            return False

        geometry = feature.geometry()
        
        # Delete the vertex
        if geometry.deleteVertex(vertex_index):
            self.layer.changeGeometry(feature_id, geometry)
            self.canvas.refresh()
            return True
        else:
            print(f"Failed to delete vertex {vertex_index}.")
            return False

    def add_vertex(self, feature_id: int, position: QgsPointXY, before_vertex_index: int = None):
        """
        Adds a vertex to a feature.
        
        :param feature_id: The feature ID.
        :param position: The position of the new vertex as QgsPointXY.
        :param before_vertex_index: Insert before this vertex index. If None, appends.
        :return: True if successful, False otherwise.
        """
        if not self.layer.isEditable():
            print("Layer is not in edit mode.")
            return False

        feature = self.layer.getFeature(feature_id)
        if not feature.isValid():
            print(f"Feature {feature_id} not found.")
            return False

        geometry = feature.geometry()
        
        # Insert the vertex
        if before_vertex_index is not None:
            success = geometry.insertVertex(position.x(), position.y(), before_vertex_index)
        else:
            # Append to the end (before the closing vertex in a polygon)
            vertex_count = len(geometry.asPolygon()[0]) if geometry.type() == QgsGeometry.PolygonGeometry else 0
            success = geometry.insertVertex(position.x(), position.y(), vertex_count - 1)

        if success:
            self.layer.changeGeometry(feature_id, geometry)
            self.canvas.refresh()
            return True
        else:
            print("Failed to add vertex.")
            return False


class SimpleVertexEditTool(QgsMapToolIdentifyFeature):
    """
    A simplified interactive vertex editing tool.
    This allows clicking on features and their vertices for basic editing.
    """
    
    vertexMoved = pyqtSignal(int, int, QgsPointXY)  # feature_id, vertex_index, new_position
    
    def __init__(self, canvas: QgsMapCanvas, layer: QgsVectorLayer):
        """
        Initializer.
        
        :param canvas: The QGIS map canvas.
        :param layer: The vector layer to edit.
        """
        super().__init__(canvas, layer)
        self.canvas = canvas
        self.layer = layer
        self.selected_feature_id = None
        self.selected_vertex_index = None
        self.dragging = False

    def canvasPressEvent(self, event):
        """Handles mouse press events."""
        if event.button() == Qt.LeftButton:
            # Identify feature at click position
            results = self.identify(event.x(), event.y(), [self.layer], self.TopDownStopAtFirst)
            
            if results:
                feature = results[0].mFeature
                self.selected_feature_id = feature.id()
                
                # Find nearest vertex
                click_point = self.toMapCoordinates(event.pos())
                geometry = feature.geometry()
                
                vertex_id = geometry.closestVertex(click_point)[1]
                self.selected_vertex_index = vertex_id
                self.dragging = True
                
                print(f"Selected vertex {vertex_id} of feature {self.selected_feature_id}")

    def canvasMoveEvent(self, event):
        """Handles mouse move events for dragging vertices."""
        if self.dragging and self.selected_feature_id is not None:
            new_position = self.toMapCoordinates(event.pos())
            
            # Update vertex position
            feature = self.layer.getFeature(self.selected_feature_id)
            geometry = feature.geometry()
            
            if geometry.moveVertex(new_position.x(), new_position.y(), self.selected_vertex_index):
                self.layer.changeGeometry(self.selected_feature_id, geometry)
                self.canvas.refresh()

    def canvasReleaseEvent(self, event):
        """Handles mouse release events."""
        if event.button() == Qt.LeftButton and self.dragging:
            new_position = self.toMapCoordinates(event.pos())
            self.vertexMoved.emit(self.selected_feature_id, self.selected_vertex_index, new_position)
            self.dragging = False
            print(f"Vertex moved to {new_position.x()}, {new_position.y()}")

    def deactivate(self):
        """Deactivates the tool."""
        super().deactivate()
        self.dragging = False
        self.selected_feature_id = None
        self.selected_vertex_index = None
