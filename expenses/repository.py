from database.connection import get_db_connection

class ExpenseRepository:

    @staticmethod
    def add(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # ✅ FIXED: removed description, added title, fixed spent_at
            cur.execute("""
                INSERT INTO expenses (society_id, title, category, amount, spent_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (
                data['society_id'],
                data.get('description', 'Expense'),  # using description as title
                data['category'],
                data['amount']
            ))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_society(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM expenses 
                WHERE society_id = %s 
                ORDER BY spent_at DESC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()