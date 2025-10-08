from .database_manager import DatabaseManager
from models.annotation import Annotation
from qgis.core import QgsGeometry
from PyQt6.QtWidgets import QMessageBox

class AnnotationManager:
    """Handles CRUD operations for annotations in the database."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializer.

        :param db_manager: An instance of the DatabaseManager.
        """
        self.db = db_manager

    def save_annotation(self, annotation: Annotation) -> bool:
        """
        Saves a new annotation to the database.

        :param annotation: The Annotation object to save.
        :return: True if successful, False otherwise.
        """
        if not self.db.is_connected():
            print("Error: Database is not connected.")
            return False

        sql = """
            INSERT INTO terrain_annotations (
                geom, class_name, class_id, area_sqm, perimeter_m,
                elevation_min, elevation_max, elevation_mean, slope_mean,
                annotator, notes, created_at, updated_at
            ) VALUES (
                ST_GeomFromText(%s, 4326), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (
                annotation.geom,
                annotation.class_name,
                annotation.class_id,
                annotation.area_sqm,
                annotation.perimeter_m,
                annotation.elevation_min,
                annotation.elevation_max,
                annotation.elevation_mean,
                annotation.slope_mean,
                annotation.annotator,
                annotation.notes,
                annotation.created_at,
                annotation.updated_at
            ))
            self.db.conn.commit()
            print("Annotation saved successfully.")
            return True
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Could not save annotation to the database.\n\nDetails: {e}")
            return False

    def update_annotation(self, annotation: Annotation) -> bool:
        """
        Updates an existing annotation in the database.

        :param annotation: The Annotation object with updated data. Its 'id' must be set.
        :return: True if successful, False otherwise.
        """
        if not self.db.is_connected() or not annotation.id:
            return False

        sql = """
            UPDATE terrain_annotations SET
                geom = ST_GeomFromText(%s, 4326),
                class_name = %s,
                area_sqm = %s,
                perimeter_m = %s,
                elevation_min = %s,
                elevation_max = %s,
                elevation_mean = %s,
                slope_mean = %s,
                updated_at = %s
            WHERE id = %s
        """
        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (
                annotation.geom, annotation.class_name, annotation.area_sqm,
                annotation.perimeter_m, annotation.elevation_min, annotation.elevation_max,
                annotation.elevation_mean, annotation.slope_mean,
                annotation.updated_at, annotation.id
            ))
            self.db.conn.commit()
            print(f"Annotation {annotation.id} updated successfully.")
            return True
        except Exception as e:
            self.db.conn.rollback()
            print(f"Error updating annotation {annotation.id}: {e}")
            return False

    def get_annotation_by_id(self, annotation_id: int) -> Annotation | None:
        """
        Retrieves a single annotation from the database by its ID.

        :param annotation_id: The ID of the annotation to retrieve.
        :return: An Annotation object or None if not found.
        """
        if not self.db.is_connected():
            print("Error: Database is not connected.")
            return None

        sql = """
            SELECT id, ST_AsText(geom), class_name, class_id, area_sqm,
                   perimeter_m, elevation_min, elevation_max, elevation_mean,
                   slope_mean, annotator, notes, created_at, updated_at
            FROM terrain_annotations WHERE id = %s
        """

        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (annotation_id,))
            row = cursor.fetchone()
            if row:
                return Annotation(
                    id=row[0], geom=row[1], class_name=row[2], class_id=row[3],
                    area_sqm=row[4], perimeter_m=row[5], elevation_min=row[6],
                    elevation_max=row[7], elevation_mean=row[8], slope_mean=row[9],
                    annotator=row[10], notes=row[11], created_at=row[12], updated_at=row[13]
                )
            else:
                return None
        except Exception as e:
            print(f"Error loading annotation {annotation_id}: {e}")
            return None

    def delete_annotation(self, annotation_id: int) -> bool:
        """
        Deletes an annotation from the database by its ID.

        :param annotation_id: The ID of the annotation to delete.
        :return: True if successful, False otherwise.
        """
        if not self.db.is_connected():
            print("Error: Database is not connected.")
            return False

        sql = "DELETE FROM terrain_annotations WHERE id = %s"

        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (annotation_id,))
            self.db.conn.commit()

            # Check if any row was actually deleted
            if cursor.rowcount > 0:
                print(f"Annotation with ID {annotation_id} deleted successfully.")
                return True
            else:
                print(f"Warning: No annotation found with ID {annotation_id}.")
                return False
        except Exception as e:
            self.db.conn.rollback()
            print(f"Error deleting annotation {annotation_id}: {e}")
            return False

    def get_all_annotations(self) -> list[Annotation]:
        """
        Retrieves all annotations from the database.

        :return: A list of Annotation objects.
        """
        if not self.db.is_connected():
            print("Error: Database is not connected.")
            return []

        sql = """
            SELECT id, ST_AsText(geom), class_name, class_id, area_sqm,
                   perimeter_m, elevation_min, elevation_max, elevation_mean,
                   slope_mean, annotator, notes, created_at, updated_at
            FROM terrain_annotations
        """

        annotations = []
        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                annotations.append(Annotation(
                    id=row[0],
                    geom=row[1],
                    class_name=row[2],
                    class_id=row[3],
                    area_sqm=row[4],
                    perimeter_m=row[5],
                    elevation_min=row[6],
                    elevation_max=row[7],
                    elevation_mean=row[8],
                    slope_mean=row[9],
                    annotator=row[10],
                    notes=row[11],
                    created_at=row[12],
                    updated_at=row[13]
                ))
            print(f"Loaded {len(annotations)} annotations from the database.")
        except Exception as e:
            print(f"Error loading annotations: {e}")

        return annotations