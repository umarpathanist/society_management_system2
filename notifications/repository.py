
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class NotificationRepository:

    @staticmethod
    def create(user_id, title, message, notif_type='system'):
        """
        FIXES: unexpected keyword argument 'user_id'
        Creates a dashboard alert for a specific user.
        """
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
            print(f"Error saving notification: {e}")
            raise e
        finally:
            cur.close()
            conn.close()

    # ... keep your other methods like get_all_by_user, delete, etc. ...

    @staticmethod
    def get_all_by_user(user_id):
        """
        FIXES AttributeError: fetches all notifications for a specific user.
        """
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
    def mark_all_read(user_id):
        """Marks all unread notifications as read for a user."""
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
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (user_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count