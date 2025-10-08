from models.terrain_class import TerrainClass
from PyQt5.QtWidgets import QMessageBox


class ClassManager:
    """Manages terrain classes in the PostGIS database."""

    def __init__(self, db_manager):
        """
        Initializer.

        :param db_manager: An instance of DatabaseManager.
        """
        self.db_manager = db_manager

    def get_all_classes(self):
        """
        Retrieves all terrain classes from the database.

        :return: List of TerrainClass objects, or empty list if error.
        """
        # Ensure database is connected
        if not self.db_manager.is_connected():
            print("Database not connected. Attempting to connect...")
            if not self.db_manager.connect():
                QMessageBox.warning(
                    None,
                    "Database Error",
                    "Could not connect to the database. Please check your connection settings."
                )
                return []

        try:
            cursor = self.db_manager.connection.cursor()
            query = """
                SELECT id, class_id, class_name, color, description
                FROM terrain_classes
                ORDER BY class_id
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            classes = []
            for row in rows:
                terrain_class = TerrainClass(
                    id=row[0],
                    class_id=row[1],
                    class_name=row[2],
                    color=row[3],
                    description=row[4]
                )
                classes.append(terrain_class)

            return classes

        except Exception as e:
            print(f"Error retrieving terrain classes: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to retrieve terrain classes:\n{str(e)}"
            )
            return []

    def add_class(self, class_name, class_id, color, description=""):
        """
        Adds a new terrain class to the database.

        :param class_name: Name of the terrain class.
        :param class_id: Unique integer ID for the class.
        :param color: Hex color code (e.g., '#FF0000').
        :param description: Optional description.
        :return: True if successful, False otherwise.
        """
        # Ensure database is connected
        if not self.db_manager.is_connected():
            print("Database not connected. Attempting to connect...")
            if not self.db_manager.connect():
                QMessageBox.warning(
                    None,
                    "Database Error",
                    "Could not connect to the database. Please check your connection settings."
                )
                return False

        try:
            cursor = self.db_manager.connection.cursor()
            query = """
                INSERT INTO terrain_classes (class_id, class_name, color, description)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (class_id, class_name, color, description))
            self.db_manager.connection.commit()
            cursor.close()

            print(f"Terrain class '{class_name}' added successfully.")
            return True

        except Exception as e:
            self.db_manager.connection.rollback()
            print(f"Error adding terrain class: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to add terrain class:\n{str(e)}"
            )
            return False

    def update_class(self, terrain_class: TerrainClass):
        """
        Updates an existing terrain class in the database.

        :param terrain_class: A TerrainClass object with updated values.
        :return: True if successful, False otherwise.
        """
        # Ensure database is connected
        if not self.db_manager.is_connected():
            print("Database not connected. Attempting to connect...")
            if not self.db_manager.connect():
                QMessageBox.warning(
                    None,
                    "Database Error",
                    "Could not connect to the database. Please check your connection settings."
                )
                return False

        try:
            cursor = self.db_manager.connection.cursor()
            query = """
                UPDATE terrain_classes
                SET class_id = %s, class_name = %s, color = %s, description = %s, updated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (
                terrain_class.class_id,
                terrain_class.class_name,
                terrain_class.color,
                terrain_class.description,
                terrain_class.id
            ))
            self.db_manager.connection.commit()
            cursor.close()

            print(f"Terrain class '{terrain_class.class_name}' updated successfully.")
            return True

        except Exception as e:
            self.db_manager.connection.rollback()
            print(f"Error updating terrain class: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to update terrain class:\n{str(e)}"
            )
            return False

    def delete_class(self, class_id):
        """
        Deletes a terrain class from the database.

        :param class_id: The primary key ID of the class to delete.
        :return: True if successful, False otherwise.
        """
        # Ensure database is connected
        if not self.db_manager.is_connected():
            print("Database not connected. Attempting to connect...")
            if not self.db_manager.connect():
                QMessageBox.warning(
                    None,
                    "Database Error",
                    "Could not connect to the database. Please check your connection settings."
                )
                return False

        try:
            cursor = self.db_manager.connection.cursor()
            query = "DELETE FROM terrain_classes WHERE id = %s"
            cursor.execute(query, (class_id,))
            self.db_manager.connection.commit()
            cursor.close()

            print(f"Terrain class with ID {class_id} deleted successfully.")
            return True

        except Exception as e:
            self.db_manager.connection.rollback()
            print(f"Error deleting terrain class: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to delete terrain class:\n{str(e)}\n\nNote: Classes with associated annotations cannot be deleted."
            )
            return False

    def get_class_by_id(self, class_id):
        """
        Retrieves a terrain class by its class_id.

        :param class_id: The class_id to search for.
        :return: TerrainClass object if found, None otherwise.
        """
        # Ensure database is connected
        if not self.db_manager.is_connected():
            print("Database not connected. Attempting to connect...")
            if not self.db_manager.connect():
                return None

        try:
            cursor = self.db_manager.connection.cursor()
            query = """
                SELECT id, class_id, class_name, color, description, created_at, updated_at
                FROM terrain_classes
                WHERE class_id = %s
            """
            cursor.execute(query, (class_id,))
            row = cursor.fetchone()
            cursor.close()

            if row:
                return TerrainClass(
                    id=row[0],
                    class_id=row[1],
                    class_name=row[2],
                    color=row[3],
                    description=row[4],
                    created_at=row[5],
                    updated_at=row[6]
                )
            return None

        except Exception as e:
            print(f"Error retrieving terrain class: {e}")
            return None

    def class_id_exists(self, class_id, exclude_id=None):
        """
        Checks if a class_id already exists in the database.

        :param class_id: The class_id to check.
        :param exclude_id: Primary key ID to exclude from the check (for updates).
        :return: True if exists, False otherwise.
        """
        # Ensure database is connected
        if not self.db_manager.is_connected():
            if not self.db_manager.connect():
                return False

        try:
            cursor = self.db_manager.connection.cursor()
            if exclude_id:
                query = "SELECT COUNT(*) FROM terrain_classes WHERE class_id = %s AND id != %s"
                cursor.execute(query, (class_id, exclude_id))
            else:
                query = "SELECT COUNT(*) FROM terrain_classes WHERE class_id = %s"
                cursor.execute(query, (class_id,))
            
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0

        except Exception as e:
            print(f"Error checking class_id existence: {e}")
            return False
