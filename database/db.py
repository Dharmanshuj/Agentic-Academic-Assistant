import os
import psycopg
from dotenv import load_dotenv  

load_dotenv()


def get_connection():
    """Create a PostgreSQL connection using the Neon DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured for PostgreSQL.")
    return psycopg.connect(database_url)
