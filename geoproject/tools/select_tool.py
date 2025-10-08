from qgis.core import QgsVectorLayer
from qgis.gui import QgsMapToolIdentifyFeature
from PyQt5.QtCore import pyqtSignal

class SelectTool(QgsMapToolIdentifyFeature):
    """A map tool to select a single feature from a layer."""

    # Signal emitted with the feature ID when a feature is selected
    featureSelected = pyqtSignal(int)

    def __init__(self, canvas, layer: QgsVectorLayer):
        """
        Initializer.

        :param canvas: The QGIS map canvas.
        :param layer: The vector layer to select features from.
        """
        super().__init__(canvas)
        self.setLayer(layer)

    def canvasReleaseEvent(self, event):
        """Overrides the mouse release event to identify features."""
        # Use the base class to identify features at the click position
        found_features = self.identify(event.x(), event.y(), self.TopDownStopAtFirst)

        if found_features:
            # Get the first identified feature
            feature = found_features[0].mFeature
            feature_id = feature.id()

            # Select the feature on the layer for visual feedback
            self.layer().selectByIds([feature_id])

            # Emit the signal with the feature ID
            self.featureSelected.emit(feature_id)
        else:
            # If no feature is clicked, clear the selection
            self.layer().removeSelection()

    def setLayer(self, layer):
        """Sets the layer this tool will identify features on."""
        super().setLayer(layer)
        self.setCursor(self.cursor()) # Use standard cursor
