from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class ReportRepository:
    
    @staticmethod
    def get_financial_summary(society_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    (SELECT COALESCE(SUM(amount), 0) FROM maintenance m 
                     JOIN flats f ON m.flat_id = f.id JOIN blocks b ON f.block_id = b.id 
                     WHERE b.society_id = %s AND m.status='paid') as total_maint,
                    (SELECT COALESCE(SUM(amount), 0) FROM other_income WHERE society_id = %s) as total_misc,
                    (SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE society_id = %s) as total_exp
            """, (society_id, society_id, society_id))
            return cur.fetchone()
        finally:
            cur.close(); conn.close()


    @staticmethod
    def get_unified_ledger(society_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT income_date as entry_date, source_name as source, amount, 'IN' as type, description 
                FROM other_income WHERE society_id = %s
                
                UNION ALL
                
                -- This part pulls from the maintenance table
                SELECT m.paid_date as entry_date, 'Maint: ' || f.flat_number as source, m.amount, 'IN' as type, m.month || ' ' || m.year as description
                FROM maintenance m 
                JOIN flats f ON m.flat_id = f.id 
                JOIN blocks b ON f.block_id = b.id 
                WHERE b.society_id = %s AND m.status = 'paid' AND m.paid_date IS NOT NULL
                
                UNION ALL
                
                SELECT expense_date as entry_date, category as source, amount, 'OUT' as type, description 
                FROM expenses WHERE society_id = %s
                
                ORDER BY entry_date DESC
            """, (society_id, society_id, society_id))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()


    @staticmethod
    def get_outstanding_dues(society_id):
        """Member Outstanding Dues report. UPDATED: Added m.id"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT m.id, u.full_name, f.flat_number, m.amount, m.month, m.year
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                JOIN users u ON f.owner_id = u.id
                WHERE b.society_id = %s AND m.status = 'unpaid'
                ORDER BY m.year DESC, m.month DESC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()