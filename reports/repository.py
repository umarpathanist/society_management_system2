# reports/repository.py
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class ReportRepository:
    @staticmethod
    def get_kpis(society_id):
        """Calculates system performance metrics for dashboard progress bars."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # 1. Occupancy Rate %
            cur.execute("""
                SELECT 
                    ROUND(
                        (COUNT(*) FILTER (WHERE is_occupied = TRUE)::numeric / 
                        NULLIF(COUNT(*), 0)::numeric) * 100, 1
                    ) as occupancy
                FROM flats f 
                JOIN blocks b ON f.block_id = b.id 
                WHERE b.society_id = %s
            """, (society_id,))
            occupancy = cur.fetchone()['occupancy'] or 0

            # 2. Collection Efficiency %
            cur.execute("""
                SELECT 
                    ROUND(
                        (SUM(amount) FILTER (WHERE status = 'paid')::numeric / 
                        NULLIF(SUM(amount), 0)::numeric) * 100, 1
                    ) as collection
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id 
                JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s
            """, (society_id,))
            collection = cur.fetchone()['collection'] or 0

            return {"occupancy": occupancy, "collection": collection}
        finally:
            cur.close()
            conn.close()
# reports/repository.py

    @staticmethod
    def get_global_kpis():
        """Calculates system-wide percentages for the Super Admin."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # 1. Global Occupancy (Occupied Flats / Total Flats in all societies)
            cur.execute("""
                SELECT 
                    ROUND((COUNT(*) FILTER (WHERE is_occupied = TRUE)::numeric / 
                    NULLIF(COUNT(*), 0)::numeric) * 100, 1) as occupancy
                FROM flats
            """)
            occ = cur.fetchone()['occupancy'] or 0

            # 2. Global Collection (Total Paid / Total Generated across all societies)
            cur.execute("""
                SELECT 
                    ROUND((SUM(amount) FILTER (WHERE status = 'paid')::numeric / 
                    NULLIF(SUM(amount), 0)::numeric) * 100, 1) as collection
                FROM maintenance
            """)
            coll = cur.fetchone()['collection'] or 0

            return {"occupancy": occ, "collection": coll}
        finally:
            cur.close(); conn.close()
    
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

    # reports/repository.py

    @staticmethod
    def get_kpis(society_id):
        """Calculates system performance metrics."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # 1. Occupancy Rate %
            cur.execute("""
                SELECT 
                    ROUND((COUNT(*) FILTER (WHERE is_occupied = TRUE)::numeric / COUNT(*)::numeric) * 100, 1) as occupancy_rate
                FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = %s
            """, (society_id,))
            occupancy = cur.fetchone()['occupancy_rate'] or 0

            # 2. Collection Efficiency % (Paid vs Total generated for last 6 months)
            cur.execute("""
                SELECT 
                    ROUND((SUM(amount) FILTER (WHERE status = 'paid')::numeric / SUM(amount)::numeric) * 100, 1) as collection_rate
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s
            """, (society_id,))
            collection = cur.fetchone()['collection_rate'] or 0

            return {"occupancy": occupancy, "collection": collection}
        finally:
            cur.close(); conn.close()