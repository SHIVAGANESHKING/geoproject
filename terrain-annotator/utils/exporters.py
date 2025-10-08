import json
from models.annotation import Annotation
from shapely.wkt import loads as wkt_loads
from shapely.geometry import mapping

class GeoJsonExporter:
    """Handles exporting annotations to GeoJSON format."""

    @staticmethod
    def export_annotations(annotations: list[Annotation], file_path: str) -> bool:
        """
        Exports a list of annotations to a GeoJSON file.

        :param annotations: A list of Annotation objects to export.
        :param file_path: The path to save the GeoJSON file to.
        :return: True if successful, False otherwise.
        """
        features = []
        for ann in annotations:
            try:
                # Convert WKT geometry to a Shapely object, then to a GeoJSON mapping
                geometry = wkt_loads(ann.geom)
                geojson_geom = mapping(geometry)

                # Create a GeoJSON feature
                feature = {
                    "type": "Feature",
                    "geometry": geojson_geom,
                    "properties": {
                        "id": ann.id,
                        "class_name": ann.class_name,
                        "class_id": ann.class_id,
                        "area_sqm": ann.area_sqm,
                        "perimeter_m": ann.perimeter_m,
                        "elevation_min": ann.elevation_min,
                        "elevation_max": ann.elevation_max,
                        "elevation_mean": ann.elevation_mean,
                        "slope_mean": ann.slope_mean,
                        "annotator": ann.annotator,
                        "notes": ann.notes,
                        "created_at": ann.created_at.isoformat(),
                        "updated_at": ann.updated_at.isoformat()
                    }
                }
                features.append(feature)
            except Exception as e:
                print(f"Could not process annotation {ann.id} for export: {e}")
                continue

        # Create the final GeoJSON FeatureCollection
        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }

        # Write to file
        try:
            with open(file_path, 'w') as f:
                json.dump(feature_collection, f, indent=2)
            print(f"Successfully exported {len(features)} annotations to {file_path}")
            return True
        except IOError as e:
            print(f"Error writing to file {file_path}: {e}")
            return False