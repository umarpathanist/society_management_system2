from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class MaintenanceRepository:
    
    @staticmethod
    def get_by_flat_id(flat_id):
        """
        Fetches all maintenance records for a specific flat.
        THIS IS THE MISSING METHOD.
        """
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
    def get_unpaid_total_by_flat(flat_id):
        """Calculates total unpaid dues for one flat."""
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


    @staticmethod
    def bulk_create_maintenance(flat_ids, amount, month, year, due_date, status='unpaid'):
        """
        Inserts multiple records. 
        FIX: Added 'status' parameter to allow manual collections to be marked as 'paid'.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = """
                INSERT INTO maintenance (flat_id, amount, month, year, due_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (flat_id, month, year) DO UPDATE SET status = EXCLUDED.status, amount = EXCLUDED.amount
            """
            for fid in flat_ids:
                # We pass the status ('paid' or 'unpaid') here
                cur.execute(query, (fid, amount, month, year, due_date, status))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    # maintenance/repository.py

    # @staticmethod
    # def mark_as_paid(maintenance_id):
    #     """Updates the status of a maintenance bill to 'paid'."""
    #     conn = get_db_connection()
    #     cur = conn.cursor()
    #     try:
    #         cur.execute("UPDATE maintenance SET status = 'paid' WHERE id = %s", (maintenance_id,))
    #         conn.commit()
    #         return True
    #     finally:
    #         cur.close()
    #         conn.close()

    # maintenance/repository.py

    @staticmethod
    def mark_as_paid(maintenance_id):
        """
        Updates status to paid AND sets the paid_date to today.
        This ensures it appears in the Financial Reports.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE maintenance 
                SET status = 'paid', 
                    paid_date = CURRENT_DATE 
                WHERE id = %s
            """, (maintenance_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    # maintenance/repository.py

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
        finally:
            cur.close()
            conn.close()


    # maintenance/repository.py

    @staticmethod
    def get_bill_status(flat_id, month, year):
        """Checks the current status of a specific maintenance bill."""
        conn = get_db_connection()
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT status FROM maintenance 
                WHERE flat_id = %s AND month = %s AND year = %s
            """, (flat_id, month, year))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()


    # maintenance/repository.py

    @staticmethod
    def get_by_id_with_flat(maintenance_id):
        """Fetches a single bill with full property context."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT m.*, f.flat_number, b.name as block_name, s.name as society_name
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                JOIN societies s ON b.society_id = s.id
                WHERE m.id = %s
            """, (maintenance_id,))
            return cur.fetchone()
        finally:
            cur.close(); conn.close()

    # maintenance/repository.py

    @staticmethod
    def get_next_unpaid_month(flat_id):
        """
        Logic: 
        1. Find the earliest 'unpaid' bill.
        2. If none, find the latest 'paid' bill and mark as 'all_paid'.
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Check for the earliest debt (unpaid)
            cur.execute("""
                SELECT month, year, 'debt' as type FROM maintenance 
                WHERE flat_id = %s AND status = 'unpaid'
                ORDER BY year ASC, 
                CASE month 
                    WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                    WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                    WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                    WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 
                END ASC LIMIT 1
            """, (flat_id,))
            res = cur.fetchone()
            if res:
                return res

            # No debt? Find the latest payment to suggest the NEXT month
            cur.execute("""
                SELECT month, year, 'all_paid' as type FROM maintenance 
                WHERE flat_id = %s AND status = 'paid'
                ORDER BY year DESC, 
                CASE month 
                    WHEN 'December' THEN 12 WHEN 'November' THEN 11 WHEN 'October' THEN 10 
                    WHEN 'September' THEN 9 WHEN 'August' THEN 8 WHEN 'July' THEN 7 
                    WHEN 'June' THEN 6 WHEN 'May' THEN 5 WHEN 'April' THEN 4 
                    WHEN 'March' THEN 3 WHEN 'February' THEN 2 WHEN 'January' THEN 1 
                END DESC LIMIT 1
            """, (flat_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()