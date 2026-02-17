# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor

# class AdminRepository:
#     @staticmethod
#     def get_all_admins():
#         """Fetches all society admins for the Super Admin list. FIXES AttributeError."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT u.id, u.full_name, u.email, u.society_id, s.name as society_name
#                 FROM users u
#                 LEFT JOIN societies s ON u.society_id = s.id
#                 WHERE u.role = 'admin'
#                 ORDER BY u.full_name ASC
#             """)
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_admin_by_society(society_id):
#         """Checks if any admin is already linked to this society."""
#         if not society_id: return None
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT full_name FROM users WHERE society_id = %s AND role = 'admin'", (society_id,))
#             return cur.fetchone()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def create_admin(data):
#         """Saves a new admin. Uses type-safe ID extraction."""
#         conn = get_db_connection()
#         cur = conn.cursor() 
#         try:
#             cur.execute("""
#                 INSERT INTO users (full_name, email, password_hash, role, society_id)
#                 VALUES (%s, %s, %s, %s, %s) RETURNING id
#             """, (data['full_name'], data['email'], data['password_hash'], 'admin', data.get('society_id')))
#             res = cur.fetchone()
#             if res:
#                 new_id = res['id'] if isinstance(res, dict) else res[0]
#                 conn.commit()
#                 return new_id
#             return None
#         except Exception as e:
#             conn.rollback()
#             raise e
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_by_id(admin_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT * FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
#             return cur.fetchone()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def assign_society(admin_id, society_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("UPDATE users SET society_id = %s WHERE id = %s AND role = 'admin'", (society_id, admin_id))
#             conn.commit()
#             return True
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def delete_admin(admin_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("DELETE FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()








from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class AdminRepository:
    @staticmethod
    def get_all_admins():
        """Fetches all society admins for the Super Admin list."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT u.id, u.full_name, u.email, u.society_id, s.name as society_name
                FROM users u
                LEFT JOIN societies s ON u.society_id = s.id
                WHERE u.role = 'admin'
                ORDER BY u.id DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(admin_id):
        """Fetches a single admin's details."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT u.id, u.full_name, u.email, u.society_id, s.name as society_name
                FROM users u
                LEFT JOIN societies s ON u.society_id = s.id
                WHERE u.id = %s AND u.role = 'admin'
            """, (admin_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def create_admin(data):
        """Saves a new admin. Uses type-safe ID extraction."""
        conn = get_db_connection()
        cur = conn.cursor() 
        try:
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role, society_id)
                VALUES (%s, %s, %s, 'admin', %s) RETURNING id
            """, (data['full_name'], data['email'], data['password_hash'], data.get('society_id')))
            res = cur.fetchone()
            if res:
                new_id = res['id'] if isinstance(res, dict) else res[0]
                conn.commit()
                return new_id
            return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    # ======================================================
    # FIXED: ADDED MISSING update_admin METHOD
    # ======================================================
    @staticmethod
    def update_admin(admin_id, data):
        """Updates the admin's name and email in the database."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users 
                SET full_name = %s, email = %s 
                WHERE id = %s AND role = 'admin'
            """, (data.get('full_name'), data.get('email'), admin_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def assign_society(admin_id, society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET society_id = %s WHERE id = %s AND role = 'admin'", (society_id, admin_id))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete_admin(admin_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_admin_by_society(society_id):
        """Helper to check if a society already has an admin."""
        if not society_id: return None
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE society_id = %s AND role = 'admin'", (society_id,))
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res