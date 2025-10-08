from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox
)

class ExportDialog(QDialog):
    """A simple dialog to confirm the export action."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Export Annotations")

        layout = QVBoxLayout(self)

        label = QLabel(
            "This will export all annotations from the database to a GeoJSON file.\n\n"
            "Do you want to proceed?"
        )
        layout.addWidget(label)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
