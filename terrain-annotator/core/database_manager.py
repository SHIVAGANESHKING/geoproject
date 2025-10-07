import psycopg2
from config.database import DB_SETTINGS

class DatabaseManager:
    """Manages the connection to the PostGIS database."""
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establishes a connection to the database."""
        if self.conn is not None and not self.conn.closed:
            print("Already connected to the database.")
            return True

        try:
            self.conn = psycopg2.connect(**DB_SETTINGS)
            self.cursor = self.conn.cursor()
            print("Database connection established successfully.")
            return True
        except psycopg2.OperationalError as e:
            print(f"Error: Could not connect to the database. {e}")
            self.conn = None
            self.cursor = None
            return False

    def disconnect(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            print("Database connection closed.")

    def is_connected(self):
        """Checks if the connection is active."""
        return self.conn is not None and not self.conn.closed

    def get_cursor(self):
        """Returns the database cursor."""
        if not self.is_connected():
            self.connect()
        return self.cursor

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()