import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """
    Returns a PostgreSQL connection that provides
    dictionary-style rows (RealDictCursor)
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "sms_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "Umar123"),
        cursor_factory=RealDictCursor
    )
