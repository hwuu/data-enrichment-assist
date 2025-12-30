"""Application configuration."""
import os

# Database configuration
# Set DB_TYPE environment variable to 'postgresql' to use PostgreSQL
DATABASE_CONFIG = {
    'type': os.getenv('DB_TYPE', 'sqlite'),

    # SQLite settings
    'path': os.getenv('DB_PATH', 'gaussdb_ops.db'),

    # PostgreSQL settings
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'gaussdb_ops'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Server configuration
SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
SERVER_PORT = int(os.getenv('SERVER_PORT', '3011'))
