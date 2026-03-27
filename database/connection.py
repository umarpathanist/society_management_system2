import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3307)),
        database=os.getenv("DB_NAME", "smsdb"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4"
    )
    return conn
