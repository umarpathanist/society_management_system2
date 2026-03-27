from database.connection import get_db_connection

class AdminRepository:

    @staticmethod
    def get_all_admins():
        conn = get_db_connection()
        cur = conn.cursor()
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
        conn = get_db_connection()
        cur = conn.cursor()
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
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # ✅ FIXED: Removed RETURNING id, using lastrowid
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role, society_id)
                VALUES (%s, %s, %s, 'admin', %s)
            """, (data['full_name'], data['email'], data['password_hash'], data.get('society_id')))
            
            new_id = cur.lastrowid  # ✅ MySQL way
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_admin(admin_id, data):
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
            cur.execute(
                "UPDATE users SET society_id = %s WHERE id = %s AND role = 'admin'",
                (society_id, admin_id)
            )
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
        if not society_id:
            return None
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT full_name FROM users WHERE society_id = %s AND role = 'admin'",
                (society_id,)
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()