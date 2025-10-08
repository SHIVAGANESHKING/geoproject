from qgis.gui import QgsVertexTool, QgsMapCanvas
from qgis.core import QgsVectorLayer

class EditTool:
    """
    A wrapper for the native QGIS Vertex Tool to simplify its use.
    """
    def __init__(self, canvas: QgsMapCanvas, layer: QgsVectorLayer):
        """
        Initializer.

        :param canvas: The QGIS map canvas.
        :param layer: The vector layer to be edited.
        """
        self.canvas = canvas
        self.layer = layer

        # The QgsVertexTool is the actual tool that handles vertex editing
        self.vertex_tool = QgsVertexTool(self.canvas)
        self.vertex_tool.setCadEnabled(True) # Enable snapping and other CAD features

    def activate(self):
        """Activates the vertex editing tool."""
        if not self.layer.isEditable():
            self.layer.startEditing()

        self.canvas.setMapTool(self.vertex_tool)

    def deactivate(self, commit_changes=True):
        """Deactivates the tool and optionally commits changes."""
        if self.layer.isEditable():
            if commit_changes:
                self.layer.commitChanges()
            else:
                self.layer.rollBack()

        # Set back to a default tool (e.g., pan tool)
        self.canvas.unsetMapTool(self.vertex_tool)

    def is_active(self):
        """Checks if the vertex tool is the current map tool."""
        return self.canvas.mapTool() is self.vertex_tool