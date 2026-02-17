# import os
# import psycopg2
# from psycopg2.extras import RealDictCursor
# from urllib.parse import urlparse






# def get_db_connection():
#     """
#     Returns a PostgreSQL connection that provides
#     dictionary-style rows (RealDictCursor)
#     """
#     return psycopg2.connect(
#         host=os.getenv("DB_HOST", "localhost"),
#         port=int(os.getenv("DB_PORT", 5432)),
#         dbname=os.getenv("DB_NAME", "sms_db"),
#         user=os.getenv("DB_USER", "postgres"),
#         password=os.getenv("DB_PASSWORD", "Umar123"),
#         cursor_factory=RealDictCursor
#     )

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """
    Returns a PostgreSQL connection. 
    Supports Render's DATABASE_URL for production and local settings for development.
    """
    # 1. Check if we are on Render (Render provides DATABASE_URL)
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        # Render URLs often start with 'postgres://'. 
        # Psycopg2 requires 'postgresql://' to avoid errors.
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        return psycopg2.connect(db_url)
    
    else:
        # 2. Local fallback for your computer
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            dbname=os.getenv("DB_NAME", "sms_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Umar123")
        )