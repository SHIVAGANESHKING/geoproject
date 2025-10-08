from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QGroupBox
)
from config.database import DB_SETTINGS

class SettingsDialog(QDialog):
    """A dialog to display application settings."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Application Settings")

        layout = QVBoxLayout(self)

        # Database Settings Group
        db_group = QGroupBox("Database Connection")
        form_layout = QFormLayout()

        # Create read-only line edits to display the settings
        self.host_edit = QLineEdit(DB_SETTINGS.get("host"))
        self.host_edit.setReadOnly(True)
        self.port_edit = QLineEdit(DB_SETTINGS.get("port"))
        self.port_edit.setReadOnly(True)
        self.dbname_edit = QLineEdit(DB_SETTINGS.get("dbname"))
        self.dbname_edit.setReadOnly(True)
        self.user_edit = QLineEdit(DB_SETTINGS.get("user"))
        self.user_edit.setReadOnly(True)

        form_layout.addRow("Host:", self.host_edit)
        form_layout.addRow("Port:", self.port_edit)
        form_layout.addRow("Database Name:", self.dbname_edit)
        form_layout.addRow("User:", self.user_edit)

        db_group.setLayout(form_layout)
        layout.addWidget(db_group)

        # OK button to close the dialog
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)