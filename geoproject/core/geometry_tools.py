"""
A collection of tools for performing spatial operations and validation on geometries.
"""
from qgis.core import QgsGeometry

def is_polygon_simple(geometry: QgsGeometry) -> bool:
    """
    Checks if a polygon is simple (doesn't self-intersect).
    
    :param geometry: QgsGeometry object
    :return: True if simple, False otherwise
    """
    if not geometry or geometry.isEmpty():
        return False
    
    return geometry.isGeosValid()
