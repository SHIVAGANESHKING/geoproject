from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QDialogButtonBox, QMessageBox, QListWidgetItem
)
from core.class_manager import ClassManager

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
        # self.add_button.clicked.connect(self.add_class)
        # self.edit_button.clicked.connect(self.edit_class)
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
            # Store the actual object in the item's data
            item.setData(1, terrain_class)
            self.list_widget.addItem(item)

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

    # TODO: Implement add_class and edit_class methods, which will likely
    # require another small dialog for input.