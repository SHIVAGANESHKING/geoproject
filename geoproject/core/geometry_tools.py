"""
A collection of tools for performing spatial operations and validation on geometries.
"""
from qgis.core import QgsGeometry

def is_polygon_simple(geometry: QgsGeometry) -> bool:
    """
    Checks if a polygon geometry is simple (i.e., does not self-intersect).

    The QGIS `isSimple()` method returns True for simple geometries. For polygons,
    this means no self-intersections.

    :param geometry: The QgsGeometry object to check.
    :return: True if the polygon is simple, False otherwise.
    """
    if not geometry or geometry.wkbType() not in [
        QgsGeometry.WkbType.Polygon, QgsGeometry.WkbType.MultiPolygon
    ]:
        # Not a polygon, so the check doesn't apply in the same way.
        return False

    return geometry.isSimple()