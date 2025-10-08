from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QRadioButton,
    QPushButton, QLabel, QFormLayout
)

class SidebarWidget(QWidget):
    """The sidebar widget for controls and information."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setFixedWidth(300)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Terrain Classes Group
        classes_group = QGroupBox("Terrain Classes")
        classes_layout = QVBoxLayout()

        # These would eventually be loaded from the database
        self.class_radios = {
            "Flat": QRadioButton("Flat"),
            "Hill": QRadioButton("Hill"),
            "Low Mountain": QRadioButton("Low Mountain"),
            "High Mountain": QRadioButton("High Mountain"),
            "Valley": QRadioButton("Valley"),
            "Ridge": QRadioButton("Ridge")
        }

        # Set first class as default
        list(self.class_radios.values())[0].setChecked(True)

        for radio in self.class_radios.values():
            classes_layout.addWidget(radio)

        classes_group.setLayout(classes_layout)
        main_layout.addWidget(classes_group)

        # 2. Drawing Tools Group
        tools_group = QGroupBox("Drawing Tools")
        tools_layout = QVBoxLayout()

        self.start_draw_button = QPushButton("Start Drawing")
        self.edit_button = QPushButton("Edit Annotation")
        self.delete_button = QPushButton("Delete Selected")

        tools_layout.addWidget(self.start_draw_button)
        tools_layout.addWidget(self.edit_button)
        tools_layout.addWidget(self.delete_button)

        tools_group.setLayout(tools_layout)
        main_layout.addWidget(tools_group)

        # 3. Statistics Panel Group
        stats_group = QGroupBox("Live Statistics")
        stats_layout = QFormLayout()

        self.area_label = QLabel("0.0 km²")
        self.perimeter_label = QLabel("0.0 km")
        self.mean_elevation_label = QLabel("N/A")
        self.mean_slope_label = QLabel("N/A")

        stats_layout.addRow("Area:", self.area_label)
        stats_layout.addRow("Perimeter:", self.perimeter_label)
        stats_layout.addRow("Mean Elevation:", self.mean_elevation_label)
        stats_layout.addRow("Mean Slope (°):", self.mean_slope_label)

        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # 4. Actions Group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        self.save_button = QPushButton("Save to PostGIS")
        self.export_button = QPushButton("Export...")

        actions_layout.addWidget(self.save_button)
        actions_layout.addWidget(self.export_button)

        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        main_layout.addStretch() # Pushes everything to the top