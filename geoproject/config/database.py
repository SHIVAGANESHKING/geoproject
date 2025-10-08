import os

# Database connection settings
DB_SETTINGS = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': os.getenv('PG_PORT', '5432'),
    'dbname': os.getenv('PG_DBNAME', 'osm_data'),
    'user': os.getenv('PG_USER', 'postgres'),
    'password': os.getenv('PG_PASSWORD', 'r0b0tic5'),
}

# Print configuration (without password) for debugging
def print_config():
    """Prints the current database configuration (without password)."""
    print("Database Configuration:")
    print(f"  Host: {DB_SETTINGS['host']}")
    print(f"  Port: {DB_SETTINGS['port']}")
    print(f"  Database: {DB_SETTINGS['dbname']}")
    print(f"  User: {DB_SETTINGS['user']}")
    print(f"  Password: {'*' * len(DB_SETTINGS['password']) if DB_SETTINGS['password'] else '(not set)'}")  "password": os.getenv("PG_PASSWORD", "password")
}
