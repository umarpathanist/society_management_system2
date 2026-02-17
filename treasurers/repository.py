# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor



# class TreasurerRepository:

    
#     @staticmethod
#     def create(data):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 INSERT INTO users (full_name, email, password_hash, role, society_id)
#                 VALUES (%s, %s, %s, %s, %s)
#                 RETURNING id
#             """, (
#                 data["full_name"],
#                 data["email"],
#                 data["password_hash"],
#                 "treasurer",
#                 data["society_id"]
#             ))
#             new_id = cur.fetchone()
#             conn.commit()
#             return new_id
#         finally:
#             cur.close()
#             conn.close()


#     @staticmethod
#     def get_all_with_societies():
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT u.id, u.full_name, u.email, s.name as society_name
#                 FROM users u
#                 LEFT JOIN societies s ON u.society_id = s.id
#                 WHERE u.role = 'treasurer'
#                 ORDER BY u.full_name
#             """)
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()


#     @staticmethod
#     def get_by_id(user_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT * FROM users WHERE id = %s AND role = 'treasurer'", (user_id,))
#             return cur.fetchone()
#         finally:
#             cur.close()
#             conn.close()


#     @staticmethod
#     def update(user_id, data):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             # Note: We only update password if a new one is provided
#             if data.get("password_hash"):
#                 cur.execute("""
#                     UPDATE users SET full_name=%s, email=%s, society_id=%s, password_hash=%s
#                     WHERE id=%s AND role='treasurer'
#                 """, (data["full_name"], data["email"], data["society_id"], data["password_hash"], user_id))
#             else:
#                 cur.execute("""
#                     UPDATE users SET full_name=%s, email=%s, society_id=%s
#                     WHERE id=%s AND role='treasurer'
#                 """, (data["full_name"], data["email"], data["society_id"], user_id))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()


#     @staticmethod
#     def delete(user_id):
        
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("DELETE FROM users WHERE id = %s AND role = 'treasurer'", (user_id,))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()




from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class TreasurerRepository:

    @staticmethod
    def create(data):
        """Saves a new treasurer. FIXES: Error 0 (KeyError)"""
        conn = get_db_connection()
        # We use a standard cursor for INSERT to ensure result[0] works
        cur = conn.cursor() 
        try:
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role, society_id)
                VALUES (%s, %s, %s, 'treasurer', %s) RETURNING id
            """, (data["full_name"], data["email"], data["password_hash"], data["society_id"]))
            
            res = cur.fetchone()
            if res:
                # SAFE CHECK: Extracts ID whether it is a dictionary or a tuple
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

    @staticmethod
    def get_treasurer_by_society(society_id):
        """Required to enforce 1 Treasurer per Society rule."""
        if not society_id: return None
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT full_name FROM users WHERE society_id = %s AND role = 'treasurer'", (society_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all_with_societies():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT u.id, u.full_name, u.email, u.society_id, s.name as society_name
                FROM users u
                LEFT JOIN societies s ON u.society_id = s.id
                WHERE u.role = 'treasurer'
                ORDER BY u.full_name ASC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM users WHERE id = %s AND role = 'treasurer'", (user_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update(user_id, data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if data.get("password_hash"):
                cur.execute("""
                    UPDATE users SET full_name=%s, email=%s, society_id=%s, password_hash=%s
                    WHERE id=%s AND role='treasurer'
                """, (data["full_name"], data["email"], data["society_id"], data["password_hash"], user_id))
            else:
                cur.execute("""
                    UPDATE users SET full_name=%s, email=%s, society_id=%s
                    WHERE id=%s AND role='treasurer'
                """, (data["full_name"], data["email"], data["society_id"], user_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE id = %s AND role = 'treasurer'", (user_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()