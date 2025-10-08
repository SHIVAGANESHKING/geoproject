import sys
from unittest.mock import MagicMock

# Create a mock for the entire 'qgis' module and its submodules
# This prevents ImportError during test collection when QGIS is not installed.
MOCK_MODULES = {
    'qgis': MagicMock(),
    'qgis.core': MagicMock(),
    'qgis.gui': MagicMock(),
    'qgis.analysis': MagicMock(),
    'processing': MagicMock(),
    'PyQt6.QtCore': MagicMock(),
    'PyQt6.QtGui': MagicMock(),
    'PyQt6.QtWidgets': MagicMock(),
}

# Check if we can import qgis, if not, apply the mocks
try:
    import qgis
    import processing
except ImportError:
    sys.modules.update(MOCK_MODULES)