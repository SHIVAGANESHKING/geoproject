import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.map_canvas import qgis_app # Import the QGIS app instance
from core.statistics import initialize_processing

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)

    # Ensure QGIS is initialized before creating the main window
    if not qgis_app:
        print("QGIS App could not be initialized. Exiting.")
        return 1

    # Initialize the QGIS processing framework
    initialize_processing()

    main_win = MainWindow()
    main_win.show()

    # Connect the cleanup function to the application's exit
    app.aboutToQuit.connect(qgis_app.exitQgis)

    exit_code = app.exec()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()