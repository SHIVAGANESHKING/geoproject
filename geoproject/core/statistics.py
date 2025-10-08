from qgis.core import (
    QgsGeometry, 
    QgsRasterLayer,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsFields
)
from qgis.analysis import QgsZonalStatistics  # ✅ FIXED: Moved from qgis.core
from qgis import processing
from PyQt5.QtCore import QVariant
import numpy as np

try:
    from qgis.analysis import QgsNativeAlgorithms
    from qgis import processing
except (ImportError, ModuleNotFoundError):
    processing = None

# Initialize QGIS processing framework
def initialize_processing():
    """Initialize the QGIS processing framework."""
    try:
        from qgis import processing
        from processing.core.Processing import Processing
        Processing.initialize()
        print("QGIS Processing framework initialized.")
        return True
    except ImportError as e:
        print(f"Warning: 'processing' module not found. Slope calculations will be disabled.")
        print(f"Error details: {e}")
        return False
    except Exception as e:
        print(f"Warning: Could not initialize QGIS Processing: {e}")
        return False


# Global flag to track if processing is available
PROCESSING_AVAILABLE = False


class StatisticsCalculator:
    """Calculates various statistics for geometries and raster data."""

    def __init__(self):
        """Initializer."""
        global PROCESSING_AVAILABLE
        # Check if processing is available
        try:
            from qgis import processing
            PROCESSING_AVAILABLE = True
        except ImportError:
            PROCESSING_AVAILABLE = False
            print("Warning: Processing module not available. Slope calculations disabled.")

    def calculate_geometry_stats(self, geometry: QgsGeometry) -> dict:
        """
        Calculates area and perimeter for a geometry.
        
        :param geometry: A QgsGeometry object.
        :return: Dictionary with 'area' (in square meters) and 'perimeter' (in meters).
        """
        if not geometry or geometry.isEmpty():
            return {'area': 0.0, 'perimeter': 0.0}

        # Area in square meters (assuming geometry is in a projected CRS)
        area = geometry.area()
        
        # Perimeter in meters
        perimeter = geometry.length()

        return {
            'area': area,
            'perimeter': perimeter
        }

    def calculate_raster_stats(self, geometry: QgsGeometry, raster_layer: QgsRasterLayer) -> dict:
        """
        Calculates elevation and slope statistics for a geometry from a raster layer.
        
        :param geometry: A QgsGeometry object (polygon).
        :param raster_layer: A QgsRasterLayer (DSM/DEM).
        :return: Dictionary with elevation and slope statistics.
        """
        if not geometry or geometry.isEmpty():
            return None

        if not raster_layer or not raster_layer.isValid():
            print("Invalid raster layer provided.")
            return None

        try:
            # Create a temporary memory layer for the geometry
            temp_layer = QgsVectorLayer("Polygon?crs=epsg:4326", "temp", "memory")
            provider = temp_layer.dataProvider()
            
            # Add fields for statistics
            fields = QgsFields()
            fields.append(QgsField("id", QVariant.Int))
            provider.addAttributes(fields)
            temp_layer.updateFields()

            # Add the geometry as a feature
            feature = QgsFeature()
            feature.setGeometry(geometry)
            feature.setAttributes([1])
            provider.addFeatures([feature])
            temp_layer.updateExtents()

            # Calculate zonal statistics using QgsZonalStatistics
            # QGIS 3.x API: QgsZonalStatistics(vectorLayer, rasterLayer, attributePrefix, band, statistics)
            zonal_stats = QgsZonalStatistics(
                temp_layer,
                raster_layer,
                'elev_',  # attribute prefix (not a keyword argument)
                1,        # band number
                QgsZonalStatistics.Mean | 
                QgsZonalStatistics.Min | 
                QgsZonalStatistics.Max |
                QgsZonalStatistics.StDev
            )
            
            result = zonal_stats.calculateStatistics(None)
            
            if result != 0:
                print(f"Zonal statistics calculation failed with code: {result}")
                return None

            # Refresh the layer to get updated attributes
            temp_layer.updateFields()
            
            # Get the statistics from the feature
            features = list(temp_layer.getFeatures())
            if not features:
                return None

            stat_feature = features[0]
            
            # Get field values - check what fields are available
            fields = stat_feature.fields()
            field_names = [field.name() for field in fields]
            
            elevation_mean = stat_feature.attribute('elev_mean') if 'elev_mean' in field_names else None
            elevation_min = stat_feature.attribute('elev_min') if 'elev_min' in field_names else None
            elevation_max = stat_feature.attribute('elev_max') if 'elev_max' in field_names else None
            elevation_std = stat_feature.attribute('elev_stdev') if 'elev_stdev' in field_names else None

            # Calculate slope statistics using QGIS processing
            slope_mean = self._calculate_slope_stats(geometry, raster_layer)

            return {
                'elevation_mean': elevation_mean if elevation_mean is not None else 0.0,
                'elevation_min': elevation_min if elevation_min is not None else 0.0,
                'elevation_max': elevation_max if elevation_max is not None else 0.0,
                'elevation_std': elevation_std if elevation_std is not None else 0.0,
                'slope_mean': slope_mean
            }

        except Exception as e:
            print(f"Error calculating raster statistics: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_slope_stats(self, geometry: QgsGeometry, raster_layer: QgsRasterLayer) -> float:
        """
        Calculates mean slope for a geometry using QGIS processing.
        
        :param geometry: A QgsGeometry object.
        :param raster_layer: A QgsRasterLayer (DSM/DEM).
        :return: Mean slope in degrees, or None if calculation fails.
        """
        global PROCESSING_AVAILABLE
        
        if not PROCESSING_AVAILABLE:
            print("Processing module not available. Skipping slope calculation.")
            return None
            
        try:
            from qgis import processing
            
            # Use QGIS processing to calculate slope
            slope_params = {
                'INPUT': raster_layer,
                'Z_FACTOR': 1,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
            
            slope_result = processing.run("native:slope", slope_params)
            slope_layer = slope_result['OUTPUT']

            if not slope_layer or not slope_layer.isValid():
                print("Slope calculation failed.")
                return None

            # Create temporary layer for zonal stats on slope
            temp_layer = QgsVectorLayer("Polygon?crs=epsg:4326", "temp_slope", "memory")
            provider = temp_layer.dataProvider()
            
            fields = QgsFields()
            fields.append(QgsField("id", QVariant.Int))
            provider.addAttributes(fields)
            temp_layer.updateFields()

            feature = QgsFeature()
            feature.setGeometry(geometry)
            feature.setAttributes([1])
            provider.addFeatures([feature])
            temp_layer.updateExtents()

            # Calculate zonal statistics for slope
            # QGIS 3.x API: positional arguments, not keywords
            zonal_stats = QgsZonalStatistics(
                temp_layer,
                slope_layer,
                'slope_',  # attribute prefix
                1,         # band number
                QgsZonalStatistics.Mean
            )
            
            result = zonal_stats.calculateStatistics(None)
            
            if result != 0:
                print(f"Slope zonal statistics failed with code: {result}")
                return None

            # Refresh the layer
            temp_layer.updateFields()
            
            features = list(temp_layer.getFeatures())
            if features:
                stat_feature = features[0]
                fields = stat_feature.fields()
                field_names = [field.name() for field in fields]
                
                if 'slope_mean' in field_names:
                    return stat_feature.attribute('slope_mean')
            
            return None

        except Exception as e:
            print(f"Error calculating slope statistics: {e}")
            import traceback
            traceback.print_exc()
            return None

    def calculate_batch_stats(self, annotations: list, raster_layer: QgsRasterLayer) -> list:
        """
        Calculates statistics for multiple annotations in batch mode.
        
        :param annotations: List of Annotation objects.
        :param raster_layer: A QgsRasterLayer (DSM/DEM).
        :return: List of dictionaries with statistics for each annotation.
        """
        results = []
        
        for annotation in annotations:
            try:
                geometry = QgsGeometry.fromWkt(annotation.geom)
                geom_stats = self.calculate_geometry_stats(geometry)
                raster_stats = self.calculate_raster_stats(geometry, raster_layer)
                
                combined_stats = {
                    'annotation_id': annotation.id,
                    **geom_stats
                }
                
                if raster_stats:
                    combined_stats.update(raster_stats)
                
                results.append(combined_stats)
                
            except Exception as e:
                print(f"Error processing annotation {annotation.id}: {e}")
                continue
        
        return results
