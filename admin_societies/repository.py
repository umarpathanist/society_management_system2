from database.connection import get_db_connection

class adminSocietyRepository:

    @staticmethod
    def assign(admin_id, society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO admin_societies (admin_id, society_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (admin_id, society_id))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_societies_for_admin(admin_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.*
            FROM societies s
            JOIN admin_societies a ON a.society_id = s.id
            WHERE a.admin_id = %s
        """, (admin_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def remove(admin_id, society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM admin_societies
            WHERE admin_id = %s AND society_id = %s
        """, (admin_id, society_id))
        conn.commit()
        cur.close()
        conn.close()
