import pytest
from unittest.mock import MagicMock

# The conftest.py file provides a mock for the 'qgis' module,
# so we can import from it without causing an ImportError.
from qgis.core import QgsZonalStatistics, QgsRasterLayer, QgsCoordinateReferenceSystem
from core.statistics import StatisticsCalculator

class MockQgsGeometry:
    """A more advanced mock for a QGIS geometry object for testing purposes."""
    def __init__(self, area, length, crs_id):
        self._area = area
        self._length = length
        self._crs = QgsCoordinateReferenceSystem(crs_id)
        self._crs.srsid.return_value = crs_id # Mocking the SRS ID

    def area(self):
        return self._area

    def length(self):
        return self._length

    def crs(self):
        return self._crs

    def transform(self, transform):
        """Mock the transform method. Does nothing for the test."""
        pass

def test_calculate_geometry_stats_no_transform():
    """Tests geometry stats when no CRS transformation is needed."""
    # Arrange
    # Both geometry and target CRS are the same (EPSG:3857)
    mock_geometry = MockQgsGeometry(area=10000.0, length=400.0, crs_id=3857)

    # Act
    stats = StatisticsCalculator.calculate_geometry_stats(mock_geometry)

    # Assert
    assert stats["area"] == 10000.0
    assert stats["perimeter"] == 400.0

def test_calculate_raster_stats_with_transform():
    """Tests raster stats when the geometry needs CRS transformation."""
    # Arrange
    mock_stats_instance = QgsZonalStatistics.return_value
    mock_stats_instance.mean.return_value = 150.5
    mock_stats_instance.min.return_value = 100.0
    mock_stats_instance.max.return_value = 200.0

    # Geometry is in WGS84 (4326), layer is in Web Mercator (3857)
    mock_geometry = MockQgsGeometry(area=10000.0, length=400.0, crs_id=4326)
    mock_dsm_layer = QgsRasterLayer()
    mock_dsm_layer.isValid.return_value = True
    mock_dsm_layer.crs.return_value = QgsCoordinateReferenceSystem("EPSG:3857")

    # Mock the processing framework's return value
    from processing import run
    run.return_value = {'OUTPUT': QgsRasterLayer()}

    # Act
    stats = StatisticsCalculator.calculate_raster_stats(mock_geometry, mock_dsm_layer)

    # Assert
    assert stats is not None
    assert stats["elevation_mean"] == 150.5
    # The method is called once for elevation stats, and once for slope stats
    assert mock_stats_instance.calculateStatistics.call_count == 2

def test_calculate_raster_stats_invalid_layer():
    """Tests that raster stats return None for an invalid layer."""
    # Arrange
    mock_geometry = MockQgsGeometry(area=10000.0, length=400.0, crs_id=4326)
    mock_dsm_layer = QgsRasterLayer()
    mock_dsm_layer.isValid.return_value = False

    # Act
    stats = StatisticsCalculator.calculate_raster_stats(mock_geometry, mock_dsm_layer)

    # Assert
    assert stats is None