from .database_manager import DatabaseManager
from models.terrain_class import TerrainClass
from PyQt6.QtWidgets import QMessageBox

class ClassManager:
    """Handles CRUD operations for terrain classes in the database."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializer.

        :param db_manager: An instance of the DatabaseManager.
        """
        self.db = db_manager

    def get_all_classes(self) -> list[TerrainClass]:
        """Retrieves all terrain classes from the database, ordered by class_id."""
        if not self.db.is_connected():
            return []

        sql = "SELECT id, class_name, class_id, color, description FROM terrain_classes ORDER BY class_id"
        classes = []
        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                classes.append(TerrainClass(
                    id=row[0], class_name=row[1], class_id=row[2],
                    color=row[3], description=row[4]
                ))
        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Could not load terrain classes.\n\nDetails: {e}")
        return classes

    def add_class(self, name: str, class_id: int, color: str) -> bool:
        """Adds a new terrain class to the database."""
        sql = "INSERT INTO terrain_classes (class_name, class_id, color) VALUES (%s, %s, %s)"
        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (name, class_id, color))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Could not add the new class.\n\nDetails: {e}")
            return False

    def update_class(self, terrain_class: TerrainClass) -> bool:
        """Updates an existing terrain class."""
        sql = """
            UPDATE terrain_classes
            SET class_name = %s, class_id = %s, color = %s, description = %s
            WHERE id = %s
        """
        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (
                terrain_class.class_name, terrain_class.class_id,
                terrain_class.color, terrain_class.description, terrain_class.id
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Could not update the class.\n\nDetails: {e}")
            return False

    def delete_class(self, class_id: int) -> bool:
        """Deletes a terrain class by its primary key id."""
        sql = "DELETE FROM terrain_classes WHERE id = %s"
        try:
            cursor = self.db.get_cursor()
            cursor.execute(sql, (class_id,))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Could not delete the class.\n\nDetails: {e}")
            return False