import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class TerrainViewer3D(QWidget):
    """A widget for displaying a 3D terrain mesh using PyVista."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        self.plotter.add_axes()
        self.plotter.add_camera_orientation_widget()

    def update_plot(self, mesh: pv.StructuredGrid):
        """
        Clears the current plot and displays a new 3D mesh.

        :param mesh: A PyVista mesh object to display.
        """
        self.plotter.clear()
        if mesh:
            # Add the mesh to the plotter with a terrain-like color map
            self.plotter.add_mesh(mesh, cmap="terrain", show_edges=True)
            self.plotter.reset_camera()
        self.plotter.update()

    def clear_plot(self):
        """Clears the 3D plot."""
        self.plotter.clear()
        self.plotter.update()