from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QDialogButtonBox, QMessageBox, QListWidgetItem
)
from core.class_manager import ClassManager
from .add_edit_class_dialog import AddEditClassDialog
from models.terrain_class import TerrainClass

class ClassManagerDialog(QDialog):
    """Dialog for managing terrain classes."""
    def __init__(self, class_manager: ClassManager, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.class_manager = class_manager
        self.setWindowTitle("Manage Terrain Classes")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.refresh_class_list()
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add...")
        self.edit_button = QPushButton("Edit...")
        self.delete_button = QPushButton("Delete")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        # Connect signals
        self.add_button.clicked.connect(self.add_class)
        self.edit_button.clicked.connect(self.edit_class)
        self.delete_button.clicked.connect(self.delete_class)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

    def refresh_class_list(self):
        """Reloads the list of classes from the database."""
        self.list_widget.clear()
        classes = self.class_manager.get_all_classes()
        for terrain_class in classes:
            item = QListWidgetItem(f"ID: {terrain_class.class_id} - {terrain_class.class_name}")
            item.setData(1, terrain_class)
            self.list_widget.addItem(item)

    def add_class(self):
        """Opens a dialog to add a new class."""
        dialog = AddEditClassDialog(parent=self)
        if dialog.exec():
            data = dialog.get_class_data()
            if self.class_manager.add_class(data['name'], data['class_id'], data['color']):
                self.refresh_class_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to add the new class.")

    def edit_class(self):
        """Opens a dialog to edit the selected class."""
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a class to edit.")
            return

        terrain_class = selected_item.data(1)
        dialog = AddEditClassDialog(terrain_class, self)
        if dialog.exec():
            data = dialog.get_class_data()
            updated_class = TerrainClass(
                id=terrain_class.id,
                class_name=data['name'],
                class_id=data['class_id'],
                color=data['color'],
                description=data['description']
            )
            if self.class_manager.update_class(updated_class):
                self.refresh_class_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to update the class.")

    def delete_class(self):
        """Deletes the selected class."""
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a class to delete.")
            return

        terrain_class = selected_item.data(1)
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the class '{terrain_class.class_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.class_manager.delete_class(terrain_class.id):
                self.refresh_class_list()
                QMessageBox.information(self, "Success", "Class deleted successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete the class from the database.")
