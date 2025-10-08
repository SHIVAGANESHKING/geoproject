from qgis.core import (
    QgsRasterLayer, QgsZonalStatistics, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsProject
)

# These imports will be mocked by conftest.py in the test environment
try:
    from qgis.analysis import QgsNativeAlgorithms
    import processing
except (ImportError, ModuleNotFoundError):
    processing = None

def initialize_processing():
    """
    Initializes the QGIS processing framework.
    This should be called once after the main QGIS app is initialized.
    """
    global processing
    if processing:
        try:
            from processing.core.Processing import Processing
            Processing.initialize()
            QgsProject.instance().addProvider(QgsNativeAlgorithms())
            print("QGIS Processing Framework Initialized.")
        except Exception as e:
            print(f"Warning: QGIS processing framework could not be initialized. Slope calculations will be disabled. Error: {e}")
            processing = None
    else:
        print("Warning: 'processing' module not found. Slope calculations will be disabled.")


class StatisticsCalculator:
    """Calculates geometric and raster statistics for a given geometry."""

    @staticmethod
    def calculate_geometry_stats(geometry):
        """
        Calculates basic geometric properties by reprojecting to a suitable CRS.
        """
        source_crs = geometry.crs()
        target_crs = QgsCoordinateReferenceSystem("EPSG:3857")
        if source_crs != target_crs:
            transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
            geometry.transform(transform)
        return {"area": geometry.area(), "perimeter": geometry.length()}

    @staticmethod
    def calculate_raster_stats(polygon_geometry, dsm_layer: QgsRasterLayer):
        """
        Calculates elevation and slope statistics from a raster layer within a polygon.
        """
        if not dsm_layer or not dsm_layer.isValid():
            return None

        if polygon_geometry.crs() != dsm_layer.crs():
            transform = QgsCoordinateTransform(
                polygon_geometry.crs(), dsm_layer.crs(), QgsProject.instance()
            )
            polygon_geometry.transform(transform)

        elevation_stats = QgsZonalStatistics(
            polygon_geometry, dsm_layer, prefix="elev_",
            stats=QgsZonalStatistics.Mean | QgsZonalStatistics.Min | QgsZonalStatistics.Max
        )
        elevation_stats.calculateStatistics(None)

        results = {
            "elevation_mean": elevation_stats.mean(),
            "elevation_min": elevation_stats.min(),
            "elevation_max": elevation_stats.max(),
            "slope_mean": None
        }

        if not processing:
            return results

        try:
            slope_result = processing.run(
                "native:slope",
                {'INPUT': dsm_layer, 'Z_FACTOR': 1.0, 'OUTPUT': 'TEMPORARY_OUTPUT'}
            )
            slope_layer = slope_result['OUTPUT']

            slope_stats = QgsZonalStatistics(
                polygon_geometry, slope_layer, prefix="slope_",
                stats=QgsZonalStatistics.Mean
            )
            slope_stats.calculateStatistics(None)
            results["slope_mean"] = slope_stats.mean()
        except Exception as e:
            print(f"Could not calculate slope. Is the GDAL provider enabled? Error: {e}")

        return results