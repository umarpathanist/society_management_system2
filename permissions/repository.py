from database.connection import get_db_connection



class PermissionRepository:

    @staticmethod
    def user_has_permission(user_id, permission_code):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 1
            FROM user_permissions
            WHERE user_id = %s
              AND permission_code = %s
        """, (user_id, permission_code))

        result = cur.fetchone()

        cur.close()
        conn.close()

        return result is not None
