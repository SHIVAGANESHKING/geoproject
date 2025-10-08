from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class TerrainViewer3D(QWidget):
    """A placeholder widget for the 3D terrain viewer."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("3D Viewer Functionality Coming Soon!")
        font = label.font()
        font.setPointSize(16)
        label.setFont(font)

        layout.addWidget(label)
