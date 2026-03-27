from database.connection import get_db_connection


class ReportRepository:

    @staticmethod
    def get_kpis(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    ROUND(
                        CAST(SUM(CASE WHEN f.is_occupied = 1 THEN 1 ELSE 0 END) AS DECIMAL(10,2)) /
                        NULLIF(COUNT(*), 0) * 100, 1
                    ) AS occupancy
                FROM flats f
                JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s
            """, (society_id,))
            occupancy = cur.fetchone()['occupancy'] or 0

            cur.execute("""
                SELECT
                    ROUND(
                        CAST(SUM(CASE WHEN m.status = 'paid' THEN m.amount ELSE 0 END) AS DECIMAL(10,2)) /
                        NULLIF(SUM(m.amount), 0) * 100, 1
                    ) AS collection
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

    @staticmethod
    def get_global_kpis():
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    ROUND(
                        CAST(SUM(CASE WHEN is_occupied = 1 THEN 1 ELSE 0 END) AS DECIMAL(10,2)) /
                        NULLIF(COUNT(*), 0) * 100, 1
                    ) AS occupancy
                FROM flats
            """)
            occ = cur.fetchone()['occupancy'] or 0

            cur.execute("""
                SELECT
                    ROUND(
                        CAST(SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS DECIMAL(10,2)) /
                        NULLIF(SUM(amount), 0) * 100, 1
                    ) AS collection
                FROM maintenance
            """)
            coll = cur.fetchone()['collection'] or 0

            return {"occupancy": occ, "collection": coll}
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_financial_summary(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    (SELECT COALESCE(SUM(m.amount), 0)
                     FROM maintenance m
                     JOIN flats f ON m.flat_id = f.id
                     JOIN blocks b ON f.block_id = b.id
                     WHERE b.society_id = %s AND m.status = 'paid') AS total_maint,

                    (SELECT COALESCE(SUM(amount), 0)
                     FROM other_income
                     WHERE society_id = %s) AS total_misc,

                    (SELECT COALESCE(SUM(amount), 0)
                     FROM expenses
                     WHERE society_id = %s) AS total_exp
            """, (society_id, society_id, society_id))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_unified_ledger(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                -- ✅ FIXED: income_date → received_at, source_name → title
                SELECT
                    received_at AS entry_date,
                    title AS source,
                    amount,
                    'IN' AS type,
                    description
                FROM other_income
                WHERE society_id = %s

                UNION ALL

                SELECT
                    m.paid_date AS entry_date,
                    CONCAT('Maint: ', f.flat_number) AS source,
                    m.amount,
                    'IN' AS type,
                    CONCAT(m.month, ' ', m.year) AS description
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s
                  AND m.status = 'paid'
                  AND m.paid_date IS NOT NULL

                UNION ALL

                -- ✅ FIXED: expense_date → spent_at
                SELECT
                    spent_at AS entry_date,
                    category AS source,
                    amount,
                    'OUT' AS type,
                    description
                FROM expenses
                WHERE society_id = %s

                ORDER BY entry_date DESC
            """, (society_id, society_id, society_id))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_outstanding_dues(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    m.id, u.full_name, f.flat_number,
                    m.amount, m.month, m.year
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                JOIN users u ON f.owner_id = u.id
                WHERE b.society_id = %s
                  AND m.status = 'unpaid'
                ORDER BY m.year DESC, m.month DESC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()