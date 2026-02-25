from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class MaintenanceRepository:
    
    # ======================================================
    # 1. RETRIEVAL METHODS (Search & Info)
    # ======================================================

    @staticmethod
    def get_by_flat_id(flat_id):
        """Fetches all maintenance records for a specific flat in sorted order."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT id, amount, month, year, due_date, status, created_at
                FROM maintenance
                WHERE flat_id = %s
                ORDER BY year DESC, 
                         CASE month
                            WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
                            WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
                            WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9
                            WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
                         END DESC
            """, (flat_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_flat_id_month_year(flat_id, month, year):
        """Checks if a maintenance record exists for a specific flat/month/year."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT * FROM maintenance 
                WHERE flat_id = %s AND month = %s AND year = %s
            """, (flat_id, month, year))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_unpaid_total_by_flat(flat_id):
        """Calculates total unpaid dues for a specific flat."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_sum 
                FROM maintenance 
                WHERE flat_id = %s AND status = 'unpaid'
            """, (flat_id,))
            result = cur.fetchone()
            return float(result['total_sum']) if result else 0.0
        finally:
            cur.close()
            conn.close()

    # maintenance/repository.py

    # maintenance/repository.py

# maintenance/repository.py

    @staticmethod
    def get_next_unpaid_month(flat_id):
        """
        Determines the starting period for a payment.
        1. Returns the oldest 'unpaid' bill (to clear debt first).
        2. If all paid, returns the month immediately AFTER the latest payment.
        3. If no history, returns the current month.
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        try:
            # STEP A: Check for the oldest UNPAID debt
            cur.execute("""
                SELECT month, year FROM maintenance 
                WHERE flat_id = %s AND status = 'unpaid'
                ORDER BY year ASC, 
                CASE month 
                    WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                    WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                    WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                    WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 
                END ASC LIMIT 1
            """, (flat_id,))
            debt = cur.fetchone()
            if debt:
                # Debt found, pay this first
                return {"month": debt['month'], "year": int(debt['year'])}

            # STEP B: If up to date, find the LATEST PAID month and calculate the NEXT one
            cur.execute("""
                SELECT month, year FROM maintenance 
                WHERE flat_id = %s AND status = 'paid'
                ORDER BY year DESC, 
                CASE month 
                    WHEN 'December' THEN 12 WHEN 'November' THEN 11 WHEN 'October' THEN 10 
                    WHEN 'September' THEN 9 WHEN 'August' THEN 8 WHEN 'July' THEN 7 
                    WHEN 'June' THEN 6 WHEN 'May' THEN 5 WHEN 'April' THEN 4 
                    WHEN 'March' THEN 3 WHEN 'February' THEN 2 WHEN 'January' THEN 1 
                END DESC LIMIT 1
            """, (flat_id,))
            last_paid = cur.fetchone()
            
            if last_paid:
                m_idx = months.index(last_paid['month'])
                # If paid till December, move to January of the NEXT year
                if m_idx == 11:
                    return {"month": "January", "year": int(last_paid['year']) + 1}
                else:
                    # Advance by one month in the same year
                    return {"month": months[m_idx + 1], "year": int(last_paid['year'])}
            
            # STEP C: Fallback to current system month if no records exist at all
            from datetime import datetime
            now = datetime.now()
            return {"month": now.strftime("%B"), "year": now.year}
            
        finally:
            cur.close()
            conn.close()


    # ======================================================
    # 2. WRITE METHODS (Create & Update)
    # ======================================================

    @staticmethod
    def bulk_create_maintenance(flat_ids, amount, month, year, due_date):
        """Batch inserts bills. Uses ON CONFLICT to prevent duplicates."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = """
                INSERT INTO maintenance (flat_id, amount, month, year, due_date, status)
                VALUES (%s, %s, %s, %s, %s, 'unpaid')
                ON CONFLICT (flat_id, month, year) DO NOTHING
            """
            for fid in flat_ids:
                cur.execute(query, (fid, amount, month, year, due_date))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def mark_as_paid_manually(flat_id, month, year):
        """Updates a specific bill to paid and records today's date."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE maintenance 
                SET status = 'paid', paid_date = CURRENT_DATE 
                WHERE flat_id = %s AND month = %s AND year = %s
            """, (flat_id, month, year))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def mark_as_paid(maintenance_id):
        """Updates status to paid by ID for the resident pay button."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE maintenance 
                SET status = 'paid', paid_date = CURRENT_DATE 
                WHERE id = %s
            """, (maintenance_id,))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()