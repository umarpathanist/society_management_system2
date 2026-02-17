# # from werkzeug.security import generate_password_hash
# # from treasurers.repository import TreasurerRepository
# # from database.connection import get_db_connection
# # from psycopg2.extras import RealDictCursor
# # from utils.mail import send_login_details # Using the helper we created

# # class TreasurerService:
    
# #     # --- USER MANAGEMENT (Super Admin View) ---

# #     @staticmethod
# #     def list_all():
# #         """Fetches all treasurers. FIXES: AttributeError list_all"""
# #         return TreasurerRepository.get_all_with_societies()

# #     @staticmethod
# #     def add_treasurer(data):
# #         """Hashes password, saves to DB, and sends email with plain password."""
# #         raw_password = data.get("password")
# #         data["password_hash"] = generate_password_hash(raw_password)
        
# #         result = TreasurerRepository.create(data)
        
# #         if result:
# #             send_login_details(
# #                 recipient_email=data['email'],
# #                 recipient_name=data['full_name'],
# #                 password=raw_password,
# #                 role="Treasurer"
# #             )
# #         return result

# #     @staticmethod
# #     def get_treasurer(user_id):
# #         return TreasurerRepository.get_by_id(user_id)

# #     @staticmethod
# #     def update_treasurer(user_id, data):
# #         if data.get("password"):
# #             data["password_hash"] = generate_password_hash(data["password"])
# #         return TreasurerRepository.update(user_id, data)

# #     @staticmethod
# #     def delete_treasurer(user_id):
# #         return TreasurerRepository.delete(user_id)

# #     # --- FINANCE DASHBOARD (Treasurer View) ---

# #     @staticmethod
# #     def get_finance_stats(society_id):
# #         """Calculates Income, Expenses, Resident counts for Dashboard."""
# #         if not society_id:
# #             return None

# #         conn = get_db_connection()
# #         cur = conn.cursor(cursor_factory=RealDictCursor)
        
# #         try:
# #             # 1. Total Paid Maintenance Income
# #             cur.execute("""
# #                 SELECT COALESCE(SUM(m.amount), 0) as total 
# #                 FROM maintenance m
# #                 JOIN flats f ON m.flat_id = f.id
# #                 JOIN blocks b ON f.block_id = b.id
# #                 WHERE b.society_id = %s AND m.status = 'paid'
# #             """, (society_id,))
# #             maint_income = cur.fetchone()['total']

# #             # 2. Total Other Income
# #             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM other_income WHERE society_id = %s", (society_id,))
# #             other_income = cur.fetchone()['total']

# #             # 3. Total Expenses
# #             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE society_id = %s", (society_id,))
# #             total_expenses = cur.fetchone()['total']

# #             # 4. Count Residents
# #             cur.execute("SELECT COUNT(*) as count FROM users WHERE society_id = %s AND role = 'owner'", (society_id,))
# #             owner_count = cur.fetchone()['count']

# #             cur.execute("SELECT COUNT(*) as count FROM users WHERE society_id = %s AND role = 'tenant'", (society_id,))
# #             tenant_count = cur.fetchone()['count']

# #             total_income = maint_income + other_income
# #             net_balance = total_income - total_expenses

# #             return {
# #                 "total_income": float(total_income),
# #                 "total_expenses": float(total_expenses),
# #                 "net_balance": float(net_balance),
# #                 "owner_count": owner_count,
# #                 "tenant_count": tenant_count
# #             }
# #         finally:
# #             cur.close()
# #             conn.close()

# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor
# from treasurers.repository import TreasurerRepository
# from werkzeug.security import generate_password_hash
# from utils.mail import send_login_details

# class TreasurerService:

#     # ======================================================
#     # 1. USER MANAGEMENT
#     # ======================================================
#     @staticmethod
#     def list_all():
#         return TreasurerRepository.get_all_with_societies()

#     @staticmethod
#     def add_treasurer(data):
#         raw_password = data.get("password")
#         data["password_hash"] = generate_password_hash(raw_password)
#         result = TreasurerRepository.create(data)
#         if result:
#             send_login_details(data['email'], data['full_name'], raw_password, "Treasurer")
#         return result

#     # ======================================================
#     # 2. FINANCE STATS (For Local Admin/Treasurer)
#     # ======================================================
#     @staticmethod
#     def get_finance_stats(society_id):
#         if not society_id: return None
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             # Paid Maintenance
#             cur.execute("""
#                 SELECT COALESCE(SUM(m.amount), 0) as total FROM maintenance m
#                 JOIN flats f ON m.flat_id = f.id JOIN blocks b ON f.block_id = b.id
#                 WHERE b.society_id = %s AND m.status = 'paid'
#             """, (society_id,))
#             maint = cur.fetchone()['total']

#             # Other Income & Expenses
#             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM other_income WHERE society_id = %s", (society_id,))
#             other = cur.fetchone()['total']
#             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE society_id = %s", (society_id,))
#             exp = cur.fetchone()['total']

#             # Resident counts
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE society_id = %s AND role = 'owner'", (society_id,))
#             owners = cur.fetchone()['count']
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE society_id = %s AND role = 'tenant'", (society_id,))
#             tenants = cur.fetchone()['count']

#             total_inc = maint + other
#             return {
#                 "total_income": float(total_inc), "total_expenses": float(exp),
#                 "net_balance": float(total_inc - exp),
#                 "owner_count": owners, "tenant_count": tenants
#             }
#         finally:
#             cur.close()
#             conn.close()

#     # ======================================================
#     # 3. GLOBAL STATS (FIXES: AttributeError get_global_stats)
#     # ======================================================
#     @staticmethod
#     def get_global_stats():
#         """Calculates system-wide financial totals for Super Admin."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM maintenance WHERE status = 'paid'")
#             maint = cur.fetchone()['total']
#             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM other_income")
#             other = cur.fetchone()['total']
#             cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses")
#             exp = cur.fetchone()['total']

#             # Resident global counts
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'owner'")
#             owners = cur.fetchone()['count']
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'tenant'")
#             tenants = cur.fetchone()['count']

#             total_inc = maint + other
#             return {
#                 "total_income": float(total_inc), "total_expenses": float(exp),
#                 "net_balance": float(total_inc - exp),
#                 "owner_count": owners, "tenant_count": tenants
#             }
#         finally:
#             cur.close()
#             conn.close()

#     # ======================================================
#     # 4. SYSTEM COUNTS (For Super Admin)
#     # ======================================================
#     @staticmethod
#     def get_super_admin_stats():
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT COUNT(*) as count FROM societies")
#             soc = cur.fetchone()['count']
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
#             adm = cur.fetchone()['count']
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'treasurer'")
#             trs = cur.fetchone()['count']
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'owner'")
#             own = cur.fetchone()['count']
#             cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'tenant'")
#             ten = cur.fetchone()['count']

#             return {
#                 "societies": soc, "admins": adm, "treasurers": trs,
#                 "owners": own, "tenants": ten
#             }
#         finally:
#             cur.close()
#             conn.close()


#     # treasurers/service.py

# class TreasurerService:
#     # ... keep your existing methods (list_all, add_treasurer, etc.) ...

#     @staticmethod
#     def delete_treasurer(user_id):
#         """
#         FIXES: AttributeError: TreasurerService has no attribute 'delete_treasurer'
#         """
#         return TreasurerRepository.delete(user_id)








from werkzeug.security import generate_password_hash
from treasurers.repository import TreasurerRepository
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from utils.mail import send_login_details

class TreasurerService:
    
    # --- USER MGMT ---

    @staticmethod
    def list_all():
        return TreasurerRepository.get_all_with_societies()

    @staticmethod
    def get_treasurer(user_id):
        return TreasurerRepository.get_by_id(user_id)

    @staticmethod
    def add_treasurer(data):
        # 1. ENFORCE 1:1 RULE: Check if society already has a treasurer
        existing = TreasurerRepository.get_treasurer_by_society(data.get("society_id"))
        if existing:
            raise ValueError(f"Society is already managed by {existing['full_name']}.")

        # 2. Create User
        raw_password = data.get("password")
        data["password_hash"] = generate_password_hash(raw_password)
        new_id = TreasurerRepository.create(data)
        
        # 3. Send Email
        if new_id:
            send_login_details(data['email'], data['full_name'], raw_password, "Treasurer")
        return new_id

    @staticmethod
    def update_treasurer(user_id, data):
        if data.get("password"):
            data["password_hash"] = generate_password_hash(data["password"])
        return TreasurerRepository.update(user_id, data)

    @staticmethod
    def delete_treasurer(user_id):
        return TreasurerRepository.delete(user_id)

    # --- DASHBOARD STATS ---

    @staticmethod
    def get_finance_stats(society_id):
        if not society_id: return None
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT COALESCE(SUM(m.amount), 0) as total FROM maintenance m
                JOIN flats f ON m.flat_id = f.id JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s AND m.status = 'paid'
            """, (society_id,))
            maint = cur.fetchone()['total']
            cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM other_income WHERE society_id = %s", (society_id,))
            other = cur.fetchone()['total']
            cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE society_id = %s", (society_id,))
            exp = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as count FROM users WHERE society_id = %s AND role = 'owner'", (society_id,))
            own = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM users WHERE society_id = %s AND role = 'tenant'", (society_id,))
            ten = cur.fetchone()['count']
            total_inc = maint + other
            return {
                "total_income": float(total_inc), "total_expenses": float(exp),
                "net_balance": float(total_inc - exp), "owner_count": own, "tenant_count": ten
            }
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_global_stats():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM maintenance WHERE status = 'paid'")
            maint = cur.fetchone()['total']
            cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM other_income")
            other = cur.fetchone()['total']
            cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses")
            exp = cur.fetchone()['total']
            total_inc = maint + other
            return {"total_income": float(total_inc), "total_expenses": float(exp), "net_balance": float(total_inc - exp)}
        finally: cur.close(); conn.close()

    @staticmethod
    def get_super_admin_stats():
        conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT COUNT(*) as count FROM societies"); soc = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'"); adm = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'treasurer'"); trs = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'owner'"); own = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'tenant'"); ten = cur.fetchone()['count']
            return {"societies": soc, "admins": adm, "treasurers": trs, "owners": own, "tenants": ten}
        finally: cur.close(); conn.close()