from database.connection import get_db_connection
from datetime import datetime

class MaintenanceRepository:

    # --- 1. RETRIEVAL METHODS ---

    @staticmethod
    def get_bill_by_id(bill_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM maintenance WHERE id = %s", (bill_id,))
        res = cur.fetchone()
        cur.close(); conn.close()
        return res

    @staticmethod
    def get_by_flat_id(flat_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM maintenance WHERE flat_id = %s 
                ORDER BY year DESC, 
                CASE month 
                    WHEN 'December' THEN 12 WHEN 'November' THEN 11 WHEN 'October' THEN 10 
                    WHEN 'September' THEN 9 WHEN 'August' THEN 8 WHEN 'July' THEN 7 
                    WHEN 'June' THEN 6 WHEN 'May' THEN 5 WHEN 'April' THEN 4 
                    WHEN 'March' THEN 3 WHEN 'February' THEN 2 WHEN 'January' THEN 1 
                END DESC
            """, (flat_id,))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    @staticmethod
    def get_unpaid_total_by_flat(flat_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM maintenance 
                WHERE flat_id = %s AND status = 'unpaid'
            """, (flat_id,))
            res = cur.fetchone()
            return float(res['total']) if res else 0.0
        finally:
            cur.close(); conn.close()

    @staticmethod
    def get_next_unpaid_bill(flat_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, month, year, amount FROM maintenance 
                WHERE flat_id = %s AND status = 'unpaid'
                ORDER BY year ASC, 
                    CASE month 
                        WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
                        WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
                        WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
                        WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 
                    END ASC LIMIT 1
            """, (flat_id,))
            return cur.fetchone()
        finally:
            cur.close(); conn.close()

    # --- 2. PAYMENT & UPDATE METHODS ---

    @staticmethod
    def mark_as_paid(maintenance_id, method='Cash', receiver_id=None, p_id=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE maintenance 
                SET status = 'paid', 
                    paid_date = NOW(),
                    payment_method = %s,
                    payment_received_by = %s,
                    razorpay_payment_id = %s
                WHERE id = %s
            """, (method, receiver_id, p_id, maintenance_id))
            conn.commit()
            return True
        finally:
            cur.close(); conn.close()

    @staticmethod
    def save_order_id(bill_id, order_id):
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            "UPDATE maintenance SET razorpay_order_id = %s WHERE id = %s",
            (order_id, bill_id)
        )
        conn.commit()
        cur.close(); conn.close()

    @staticmethod
    def complete_payment(bill_id, payment_id, signature):
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("""
            UPDATE maintenance 
            SET status = 'paid', 
                paid_date = CURRENT_DATE,
                payment_method = 'Online',
                razorpay_payment_id = %s, 
                razorpay_signature = %s 
            WHERE id = %s
        """, (payment_id, signature, bill_id))
        conn.commit()
        cur.close(); conn.close()

    # --- 3. BULK GENERATION ---

    @staticmethod
    def bulk_create_maintenance(flat_ids, amount, month, year, due_date):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            for fid in flat_ids:
                # ✅ FIXED: MySQL uses INSERT IGNORE instead of ON CONFLICT DO NOTHING
                cur.execute("""
                    INSERT IGNORE INTO maintenance (flat_id, amount, month, year, due_date, status)
                    VALUES (%s, %s, %s, %s, %s, 'unpaid')
                """, (fid, amount, month, year, due_date))
            conn.commit()
        finally:
            cur.close(); conn.close()

    @staticmethod
    def process_advance_payment(flat_id, start_date, end_date, amount, method, receiver_id=None):
        conn = get_db_connection(); cur = conn.cursor()
        from dateutil.relativedelta import relativedelta
        MONTHS = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        try:
            curr = datetime.strptime(start_date, '%Y-%m-%d')
            end  = datetime.strptime(end_date,   '%Y-%m-%d')
            while curr <= end:
                m_name = MONTHS[curr.month - 1]

                # ✅ FIXED: MySQL uses INSERT INTO ... ON DUPLICATE KEY UPDATE
                cur.execute("""
                    INSERT INTO maintenance 
                        (flat_id, amount, month, year, due_date, status, payment_method, paid_date, payment_received_by)
                    VALUES 
                        (%s, %s, %s, %s, %s, 'paid', %s, CURRENT_DATE, %s)
                    ON DUPLICATE KEY UPDATE 
                        status = 'paid',
                        payment_method = VALUES(payment_method),
                        paid_date = CURRENT_DATE,
                        payment_received_by = VALUES(payment_received_by),
                        amount = VALUES(amount)
                """, (flat_id, amount, m_name, curr.year, curr.strftime('%Y-%m-10'), method, receiver_id))

                curr += relativedelta(months=1)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close(); conn.close()

    # --- 4. INVOICE & LOOKUP METHODS ---

    @staticmethod
    def get_by_flat_id_month_year(flat_id, month, year):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM maintenance 
                WHERE flat_id = %s AND month = %s AND year = %s
            """, (flat_id, month, int(year)))
            return cur.fetchone()
        finally:
            cur.close(); conn.close()

    @staticmethod
    def mark_as_paid_manually(flat_id, month, year):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE maintenance 
                SET status = 'paid', 
                    paid_date = NOW(),
                    payment_method = 'Cash'
                WHERE flat_id = %s AND month = %s AND year = %s
            """, (flat_id, month, int(year)))
            conn.commit()
            return True
        finally:
            cur.close(); conn.close()

    @staticmethod
    def get_full_invoice_data(maintenance_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 
                    m.id, m.amount, m.month, m.year, m.status, m.due_date, m.paid_date,
                    f.flat_number,
                    b.name as block_name,
                    s.id as society_id, s.name as society_name, s.address as society_address,
                    COALESCE(ut.full_name, uo.full_name, 'Resident') as recipient_name,
                    COALESCE(ut.email, uo.email) as recipient_email
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                JOIN societies s ON b.society_id = s.id
                LEFT JOIN users uo ON f.owner_id = uo.id
                LEFT JOIN users ut ON f.tenant_id = ut.id
                WHERE m.id = %s
            """, (maintenance_id,))
            return cur.fetchone()
        finally:
            cur.close(); conn.close()