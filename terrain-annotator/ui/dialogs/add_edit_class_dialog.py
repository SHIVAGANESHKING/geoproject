from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QPushButton, QColorDialog, QDialogButtonBox
)
from PyQt6.QtGui import QColor, QPalette
from models.terrain_class import TerrainClass

class AddEditClassDialog(QDialog):
    """A dialog for adding or editing a terrain class."""
    def __init__(self, terrain_class: TerrainClass = None, parent=None):
        """
        Initializer.

        :param terrain_class: A TerrainClass object to edit, or None to add a new one.
        """
        super().__init__(parent)

        self.terrain_class = terrain_class
        self.setWindowTitle("Edit Class" if self.terrain_class else "Add New Class")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.id_spinbox = QSpinBox()
        self.id_spinbox.setRange(1, 999)
        self.color_button = QPushButton()
        self.color_button.clicked.connect(self.choose_color)
        self.description_edit = QLineEdit()

        form_layout.addRow("Class Name:", self.name_edit)
        form_layout.addRow("Class ID:", self.id_spinbox)
        form_layout.addRow("Color:", self.color_button)
        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        # Populate fields if editing
        if self.terrain_class:
            self.name_edit.setText(self.terrain_class.class_name)
            self.id_spinbox.setValue(self.terrain_class.class_id)
            self.set_button_color(QColor(self.terrain_class.color))
            self.description_edit.setText(self.terrain_class.description)
        else:
            self.set_button_color(QColor("white"))

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

    def choose_color(self):
        """Opens a color picker dialog."""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.set_button_color(color)

    def set_button_color(self, color: QColor):
        """Sets the background color and text for the color button."""
        self.current_color = color
        self.color_button.setText(color.name())
        palette = self.color_button.palette()
        palette.setColor(QPalette.ColorRole.Button, color)
        self.color_button.setPalette(palette)
        self.color_button.setAutoFillBackground(True)

    def get_class_data(self) -> dict:
        """Returns the data entered in the dialog."""
        return {
            "name": self.name_edit.text(),
            "class_id": self.id_spinbox.value(),
            "color": self.current_color.name(),
            "description": self.description_edit.text()
        }