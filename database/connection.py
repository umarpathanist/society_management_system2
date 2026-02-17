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
    # 1. Get the URL from Render Environment
    db_url = os.getenv("DATABASE_URL")

    try:
        if db_url:
            # Fix for Render's 'postgres://' vs 'postgresql://' requirement
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            # CRITICAL: Added cursor_factory=RealDictCursor here
            return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        
        else:
            # 2. Local fallback
            return psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                dbname=os.getenv("DB_NAME", "sms_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "Umar123"),
                cursor_factory=RealDictCursor
            )
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        raise e