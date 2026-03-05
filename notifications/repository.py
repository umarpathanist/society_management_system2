from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class NotificationRepository:

    @staticmethod
    def create(user_id, title, message, notif_type='system'):
        """Creates a dashboard alert for a specific user."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO notifications (user_id, title, message, notif_type)
                VALUES (%s, %s, %s, %s)
            """, (user_id, title, message, notif_type))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all_by_user(user_id):
        """Fetches all notifications for a specific user."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT id, title, message, notif_type, is_read, created_at 
                FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def mark_single_read(notif_id):
        """Marks one notification as read."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notif_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def mark_multiple_read(notif_ids):
        """Marks a list of notifications as read."""
        if not notif_ids: return
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Convert list to tuple for SQL 'IN' clause
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE id IN %s", (tuple(notif_ids),))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def mark_all_read(user_id):
        """Marks every notification for a user as read. (FIXED MISSING METHOD)"""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(notif_id, user_id):
        """Deletes a single notification."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM notifications WHERE id = %s AND user_id = %s", (notif_id, user_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete_all(user_id):
        """Clears the entire inbox for a user."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_unread_count(user_id):
        """Returns the number of unread notifications for a user."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (user_id,))
            return cur.fetchone()[0]
        finally:
            cur.close()
            conn.close()

    # admin/repository.py

@staticmethod
def get_admins_by_society(society_id):
    """Returns a list of user IDs for all Admins in a specific society."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM users WHERE society_id = %s AND role = 'admin'", (society_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()