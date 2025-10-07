import os

# PostGIS Connection Settings
#
# The application reads its database configuration from environment variables.
# For local development, you can set these variables in your shell or use a .env file.
#
# Required environment variables:
# - PG_HOST: The database host.
# - PG_PORT: The port for the database connection.
# - PG_DBNAME: The name of the database.
# - PG_USER: The username for the database connection.
# - PG_PASSWORD: The password for the database user.

DB_SETTINGS = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "dbname": os.getenv("PG_DBNAME", "gis_database"),
    "user": os.getenv("PG_USER", "user"),
    "password": os.getenv("PG_PASSWORD", "password")
}