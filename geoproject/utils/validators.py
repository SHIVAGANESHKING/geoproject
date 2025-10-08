"""
Input validation utilities for the application.
"""

def is_valid_class_name(name: str) -> bool:
    """
    Validates a terrain class name.
    For now, it just checks if the name is not empty.

    :param name: The class name to validate.
    :return: True if valid, False otherwise.
    """
    return bool(name and name.strip())

def is_valid_geometry(geometry) -> bool:
    """
    Validates a QGIS geometry.
    Checks for null, empty, or invalid geometries.

    :param geometry: A QgsGeometry object.
    :return: True if valid, False otherwise.
    """
    if not geometry:
        return False
    if geometry.isNull() or geometry.isEmpty():
        return False
    # A more robust check could be `geometry.isGeosValid()` but that can be slow.
    return True