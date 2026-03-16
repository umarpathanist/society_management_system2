from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class IncomeRepository:

    # ======================================================
    # 1. ADD MISC INCOME (Donations, etc.)
    # ======================================================
    @staticmethod
    def add(data):
        """Inserts a record into the other_income table."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO other_income (society_id, source_name, amount, income_date, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['society_id'], 
                data['source_name'], 
                data['amount'], 
                data['income_date'], 
                data['description']
            ))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    # ======================================================
    # 2. FETCH UNIFIED LEDGER (FIXES THE ERROR)
    # ======================================================
    # income/repository.py

    @staticmethod
    def get_combined_ledger(society_id):
        """
        FETCHES A UNIFIED LEDGER:
        - Removes Block Name from details.
        - Includes Month/Year in the period field.
        """
        if not society_id: return []

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                -- Part A: Get Miscellaneous Income
                (SELECT 
                    income_date as tr_date, 
                    source_name as category, 
                    'Direct Entry' as period,
                    COALESCE(description, 'General Receipt') as description, 
                    amount
                FROM other_income 
                WHERE society_id = %s)

                UNION ALL

                -- Part B: Get Paid Maintenance
                (SELECT 
                    m.paid_date as tr_date, 
                    'Maintenance' as category,
                    CONCAT(m.month, ' ', m.year) as period, -- Month Year for the badge
                    CONCAT('Flat ', f.flat_number) as description, -- REMOVED Block info here
                    m.amount
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s AND m.status = 'paid' AND m.paid_date IS NOT NULL)

                ORDER BY tr_date DESC
            """, (society_id, society_id))
            
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

            
    @staticmethod
    def add(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO other_income (society_id, source_name, amount, income_date, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['society_id'], data['source_name'], data['amount'], data['income_date'], data['description']))
            conn.commit()
        finally:
            cur.close(); conn.close()
