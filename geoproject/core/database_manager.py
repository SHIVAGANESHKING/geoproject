import psycopg2
from psycopg2 import sql
from PyQt5.QtWidgets import QMessageBox
import os


class DatabaseManager:
    """Manages the connection to the PostGIS database."""

    def __init__(self):
        """Initializer."""
        self.connection = None
        self.db_config = self._load_db_config()
        
        # Try to connect automatically on initialization
        self.connect()

    def _load_db_config(self):
        """
        Loads database configuration from environment variables.
        
        :return: Dictionary with database configuration.
        """
        config = {
            'host': os.getenv('PG_HOST', 'localhost'),
            'port': os.getenv('PG_PORT', '5432'),
            'dbname': os.getenv('PG_DBNAME', 'osm_data'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', 'r0b0tic5')
        }
        
        print(f"Database config loaded: {config['user']}@{config['host']}:{config['port']}/{config['dbname']}")
        return config

    def connect(self):
        """
        Establishes a connection to the PostgreSQL database.
        
        :return: True if successful, False otherwise.
        """
        if self.is_connected():
            print("Already connected to database.")
            return True

        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                dbname=self.db_config['dbname'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            print(f"Connected to database '{self.db_config['dbname']}' successfully.")
            return True

        except psycopg2.Error as e:
            error_msg = f"Database connection failed:\n{str(e)}\n\n"
            error_msg += f"Host: {self.db_config['host']}\n"
            error_msg += f"Port: {self.db_config['port']}\n"
            error_msg += f"Database: {self.db_config['dbname']}\n"
            error_msg += f"User: {self.db_config['user']}\n\n"
            error_msg += "Please check:\n"
            error_msg += "1. PostgreSQL is running\n"
            error_msg += "2. Database exists\n"
            error_msg += "3. Credentials are correct\n"
            error_msg += "4. PostGIS extension is enabled\n"
            
            print(error_msg)
            QMessageBox.critical(
                None,
                "Database Connection Error",
                error_msg
            )
            return False

        except Exception as e:
            error_msg = f"Unexpected error connecting to database:\n{str(e)}"
            print(error_msg)
            QMessageBox.critical(
                None,
                "Database Error",
                error_msg
            )
            return False

    def disconnect(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Database connection closed.")

    def is_connected(self):
        """
        Checks if the database connection is active.
        
        :return: True if connected, False otherwise.
        """
        if self.connection is None:
            return False
        
        try:
            # Try to execute a simple query to verify connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            self.connection = None
            return False

    def test_connection(self):
        """
        Tests the database connection and PostGIS availability.
        
        :return: Tuple (success: bool, message: str)
        """
        if not self.is_connected():
            if not self.connect():
                return False, "Could not establish database connection."

        try:
            cursor = self.connection.cursor()
            
            # Check PostGIS extension
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'postgis'
                )
            """)
            postgis_installed = cursor.fetchone()[0]
            
            if not postgis_installed:
                cursor.close()
                return False, "PostGIS extension is not installed in the database."

            # Check if required tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('terrain_classes', 'terrain_annotations')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()

            missing_tables = []
            if 'terrain_classes' not in tables:
                missing_tables.append('terrain_classes')
            if 'terrain_annotations' not in tables:
                missing_tables.append('terrain_annotations')

            if missing_tables:
                return False, f"Missing required tables: {', '.join(missing_tables)}"

            return True, "Database connection successful. All required tables exist."

        except Exception as e:
            return False, f"Error testing database: {str(e)}"

    def create_tables(self):
        """
        Creates the required database tables if they don't exist.
        
        :return: True if successful, False otherwise.
        """
        if not self.is_connected():
            if not self.connect():
                return False

        try:
            cursor = self.connection.cursor()

            # Create terrain_classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terrain_classes (
                    id SERIAL PRIMARY KEY,
                    class_id INTEGER UNIQUE NOT NULL,
                    class_name VARCHAR(100) NOT NULL,
                    color VARCHAR(7) DEFAULT '#FFFFFF',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create terrain_annotations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terrain_annotations (
                    id SERIAL PRIMARY KEY,
                    geom GEOMETRY(Polygon, 4326) NOT NULL,
                    class_id INTEGER REFERENCES terrain_classes(class_id),
                    class_name VARCHAR(100),
                    area_sqm DOUBLE PRECISION,
                    perimeter_m DOUBLE PRECISION,
                    elevation_min DOUBLE PRECISION,
                    elevation_max DOUBLE PRECISION,
                    elevation_mean DOUBLE PRECISION,
                    slope_mean DOUBLE PRECISION,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create spatial index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terrain_annotations_geom 
                ON terrain_annotations USING GIST(geom)
            """)

            self.connection.commit()
            cursor.close()

            print("Database tables created successfully.")
            return True

        except Exception as e:
            self.connection.rollback()
            print(f"Error creating tables: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to create database tables:\n{str(e)}"
            )
            return False

    def insert_default_classes(self):
        """
        Inserts default terrain classes if the table is empty.
        
        :return: True if successful, False otherwise.
        """
        if not self.is_connected():
            if not self.connect():
                return False

        try:
            cursor = self.connection.cursor()

            # Check if classes already exist
            cursor.execute("SELECT COUNT(*) FROM terrain_classes")
            count = cursor.fetchone()[0]

            if count > 0:
                print("Terrain classes already exist in database.")
                cursor.close()
                return True

            # Insert default classes
            default_classes = [
                (1, 'Hill', '#8B4513', 'Elevated terrain feature'),
                (2, 'Valley', '#90EE90', 'Low-lying area between hills'),
                (3, 'Plain', '#F5DEB3', 'Flat or gently rolling terrain'),
                (4, 'Ridge', '#A0522D', 'Long, narrow elevated terrain'),
                (5, 'Plateau', '#DEB887', 'Elevated flat terrain'),
            ]

            cursor.executemany(
                """
                INSERT INTO terrain_classes (class_id, class_name, color, description)
                VALUES (%s, %s, %s, %s)
                """,
                default_classes
            )

            self.connection.commit()
            cursor.close()

            print(f"Inserted {len(default_classes)} default terrain classes.")
            return True

        except Exception as e:
            self.connection.rollback()
            print(f"Error inserting default classes: {e}")
            return False

    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.disconnect()
