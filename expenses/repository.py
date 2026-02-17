from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class ExpenseRepository:
    
    @staticmethod
    def add(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO expenses (society_id, category, amount, expense_date, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['society_id'], 
                data['category'], 
                data['amount'], 
                data['expense_date'], 
                data['description']
            ))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_society(society_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM expenses WHERE society_id = %s ORDER BY expense_date DESC", (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()