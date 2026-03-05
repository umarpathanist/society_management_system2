# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor
# from datetime import datetime

# class MaintenanceRepository:

#     # ======================================================
#     # 1. RETRIEVAL METHODS (Reading Data)
#     # ======================================================

#     @staticmethod
#     def get_by_flat_id(flat_id):
#         """Fetches all bills for the resident list page, sorted by newest first."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT * FROM maintenance 
#                 WHERE flat_id = %s 
#                 ORDER BY year DESC, 
#                          CASE month 
#                             WHEN 'December' THEN 12 WHEN 'November' THEN 11 WHEN 'October' THEN 10 
#                             WHEN 'September' THEN 9 WHEN 'August' THEN 8 WHEN 'July' THEN 7 
#                             WHEN 'June' THEN 6 WHEN 'May' THEN 5 WHEN 'April' THEN 4 
#                             WHEN 'March' THEN 3 WHEN 'February' THEN 2 WHEN 'January' THEN 1 
#                          END DESC
#             """, (flat_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_unpaid_total_by_flat(flat_id):
#         """Calculates total outstanding balance for the dashboard."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT COALESCE(SUM(amount), 0) as total_sum 
#                 FROM maintenance 
#                 WHERE flat_id = %s AND status = 'unpaid'
#             """, (flat_id,))
#             result = cur.fetchone()
#             return float(result['total_sum']) if result else 0.0
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_bill_by_id(bill_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT * FROM maintenance WHERE id = %s", (bill_id,))
#             return cur.fetchone()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_next_unpaid_bill(flat_id):
#         """Used by the Collection Hub to find where to start billing."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT id, month, year, amount FROM maintenance 
#                 WHERE flat_id = %s AND status = 'unpaid'
#                 ORDER BY year ASC, 
#                     CASE month 
#                         WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3 
#                         WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6 
#                         WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9 
#                         WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12 
#                     END ASC LIMIT 1
#             """, (flat_id,))
#             return cur.fetchone()
#         finally:
#             cur.close(); conn.close()

#     # ======================================================
#     # 2. WRITE METHODS (Updating & Creating)
#     # ======================================================

#     @staticmethod
#     def mark_as_paid(maintenance_id, method='Cash', receiver_id=None, p_id=None):
#         """
#         Updates a bill to 'paid' and records the date.
#         CRITICAL: This allows the record to show in the Income Ledger.
#         """
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("""
#                 UPDATE maintenance 
#                 SET status = 'paid', 
#                     paid_date = CURRENT_DATE, 
#                     payment_method = %s,
#                     payment_received_by = %s,
#                     razorpay_payment_id = %s
#                 WHERE id = %s
#             """, (method, receiver_id, p_id, maintenance_id))
#             conn.commit()
#             return True
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def bulk_create_maintenance(flat_ids, amount, month, year, due_date):
#         """Standard monthly generation with duplicate prevention."""
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             query = """
#                 INSERT INTO maintenance (flat_id, amount, month, year, due_date, status)
#                 VALUES (%s, %s, %s, %s, %s, 'unpaid')
#                 ON CONFLICT (flat_id, month, year) DO NOTHING
#             """
#             for fid in flat_ids:
#                 cur.execute(query, (fid, amount, month, year, due_date))
#             conn.commit()
#             return True
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def process_advance_payment(flat_id, start_date, end_date, amount, method, receiver_id=None):
#         """Handles date-range payments from the Collection Hub."""
#         conn = get_db_connection()
#         cur = conn.cursor()
        
#         from dateutil.relativedelta import relativedelta
#         MONTH_MAP = {1:"January", 2:"February", 3:"March", 4:"April", 5:"May", 6:"June", 
#                      7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"December"}

#         try:
#             # Parse dates
#             start_dt = datetime.strptime(start_date, '%Y-%m-%d')
#             end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
#             curr = start_dt
#             while curr <= end_dt:
#                 m_name = MONTH_MAP[curr.month]
#                 y_num = curr.year
#                 due_date = curr.strftime('%Y-%m-10')

#                 # UPSERT logic: Updates existing or creates new paid record
#                 cur.execute("""
#                     INSERT INTO maintenance (flat_id, amount, month, year, due_date, status, payment_method, paid_date, payment_received_by)
#                     VALUES (%s, %s, %s, %s, %s, 'paid', %s, CURRENT_DATE, %s)
#                     ON CONFLICT (flat_id, month, year) 
#                     DO UPDATE SET 
#                         status = 'paid', 
#                         payment_method = EXCLUDED.payment_method, 
#                         paid_date = CURRENT_DATE,
#                         payment_received_by = EXCLUDED.payment_received_by,
#                         amount = EXCLUDED.amount
#                 """, (flat_id, amount, m_name, y_num, due_date, method, receiver_id))
                
#                 curr += relativedelta(months=1)
            
#             conn.commit()
#             return True
#         except Exception as e:
#             conn.rollback()
#             raise e
#         finally:
#             cur.close(); conn.close()

#     # --- RAZORPAY HELPERS ---

#     @staticmethod
#     def save_order_id(bill_id, order_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("UPDATE maintenance SET razorpay_order_id = %s WHERE id = %s", (order_id, bill_id))
#             conn.commit()
#         finally:
#             cur.close(); conn.close()

#     @staticmethod
#     def complete_payment(bill_id, payment_id, signature):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("""
#                 UPDATE maintenance 
#                 SET status = 'paid', 
#                     paid_date = CURRENT_DATE,
#                     payment_method = 'Online',
#                     razorpay_payment_id = %s, 
#                     razorpay_signature = %s 
#                 WHERE id = %s
#             """, (payment_id, signature, bill_id))
#             conn.commit()
#         finally:
#             cur.close(); conn.close()



from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime

class MaintenanceRepository:

    # --- 1. RETRIEVAL METHODS ---

    @staticmethod
    def get_bill_by_id(bill_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM maintenance WHERE id = %s", (bill_id,))
        res = cur.fetchone()
        cur.close(); conn.close()
        return res

    @staticmethod
    def get_by_flat_id(flat_id):
        """Fetches all bills for a resident's list."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM maintenance WHERE flat_id = %s AND status = 'unpaid'", (flat_id,))
            res = cur.fetchone()
            return float(res['total']) if res else 0.0
        finally:
            cur.close(); conn.close()

    @staticmethod
    def get_next_unpaid_bill(flat_id):
        """Used by the Collection Hub."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
        """
        Updates bill and sets paid_date. 
        CRITICAL: This ensures it appears in the Income Ledger.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE maintenance 
                SET status = 'paid', 
                    paid_date = CURRENT_DATE, 
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
        cur.execute("UPDATE maintenance SET razorpay_order_id = %s WHERE id = %s", (order_id, bill_id))
        conn.commit()
        cur.close(); conn.close()

    @staticmethod
    def complete_payment(bill_id, payment_id, signature):
        conn = get_db_connection(); cur = conn.cursor()
        # CRITICAL: paid_date is set so it shows in the Income Ledger
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
            query = """
                INSERT INTO maintenance (flat_id, amount, month, year, due_date, status)
                VALUES (%s, %s, %s, %s, %s, 'unpaid')
                ON CONFLICT (flat_id, month, year) DO NOTHING
            """
            for fid in flat_ids:
                cur.execute(query, (fid, amount, month, year, due_date))
            conn.commit()
        finally: cur.close(); conn.close()

    @staticmethod
    def process_advance_payment(flat_id, start_date, end_date, amount, method, receiver_id=None):

        conn = get_db_connection(); cur = conn.cursor()
        from dateutil.relativedelta import relativedelta
        MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        try:
            curr = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            while curr <= end:
                m_name = MONTHS[curr.month - 1]
                cur.execute("""
                    INSERT INTO maintenance (flat_id, amount, month, year, due_date, status, payment_method, paid_date, payment_received_by)
                    VALUES (%s, %s, %s, %s, %s, 'paid', %s, CURRENT_DATE, %s)
                    ON CONFLICT (flat_id, month, year) 
                    DO UPDATE SET status = 'paid', payment_method = EXCLUDED.payment_method, paid_date = CURRENT_DATE
                """, (flat_id, amount, m_name, curr.year, curr.strftime('%Y-%m-10'), method, receiver_id))
                curr += relativedelta(months=1)
            conn.commit()
        finally: cur.close(); conn.close()
        
# maintenance/repository.py

    @staticmethod
    def get_full_invoice_data(maintenance_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    -- Maintenance Details
                    m.id,                -- CHANGED: Removed 'as maintenance_id'
                    m.amount,
                    m.month,
                    m.year,
                    m.status,
                    m.due_date,
                    m.paid_date,
                    
                    -- Flat & Block Details
                    f.flat_number,
                    b.name as block_name,
                    
                    -- Society Details
                    s.id as society_id,
                    s.name as society_name,
                    s.address as society_address,
                    
                    -- User (Owner/Payer) Details
                    COALESCE(u.full_name, 'Resident') as owner_name, -- Added fallback for 'None'
                    u.email as owner_email
                    
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                JOIN societies s ON b.society_id = s.id
                LEFT JOIN users u ON f.owner_id = u.id
                WHERE m.id = %s
            """, (maintenance_id,))
            
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()