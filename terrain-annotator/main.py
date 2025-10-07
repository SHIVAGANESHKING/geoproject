import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()