from database.connection import get_db_connection

class IncomeRepository:

    @staticmethod
    def add(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO other_income (society_id, title, amount, received_at, description)
                VALUES (%s, %s, %s, NOW(), %s)
            """, (
                data['society_id'],
                data['source_name'],
                data['amount'],
                # ✅ REMOVED data['income_date'] — NOW() handles it
                data['description']
            ))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_combined_ledger(society_id):
        if not society_id: return []
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                -- Part A: Miscellaneous Income
                (SELECT
                    received_at as tr_date,
                    title as category,
                    'Direct Entry' as period,
                    COALESCE(description, 'General Receipt') as description,
                    amount
                FROM other_income
                WHERE society_id = %s)
                UNION ALL
                -- Part B: Paid Maintenance
                (SELECT
                    m.paid_date as tr_date,
                    'Maintenance' as category,
                    CONCAT(m.month, ' ', m.year) as period,
                    CONCAT('Flat ', f.flat_number) as description,
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