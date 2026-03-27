from database.connection import get_db_connection

class TicketRepository:

    @staticmethod
    def create(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # ✅ FIXED: Removed RETURNING id, using lastrowid
            cur.execute("""
                INSERT INTO tickets (user_id, society_id, title, description, category, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data['user_id'], data['society_id'], data['title'],
                data['description'], data['category'], data['priority']
            ))
            new_id = cur.lastrowid  # ✅ MySQL way
            conn.commit()
            return new_id
        except Exception as e:
            conn.rollback()
            print(f"DATABASE ERROR: {e}")
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(ticket_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT t.*, u.full_name as creator_name, u.email as owner_email
                FROM tickets t 
                JOIN users u ON t.user_id = u.id 
                WHERE t.id = %s
            """, (ticket_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_society(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT t.*, u.full_name as creator_name 
                FROM tickets t JOIN users u ON t.user_id = u.id 
                WHERE t.society_id = %s ORDER BY t.created_at DESC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM tickets WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_comments(ticket_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT tc.*, u.full_name as user_name 
                FROM ticket_comments tc 
                JOIN users u ON tc.user_id = u.id 
                WHERE tc.ticket_id = %s ORDER BY tc.created_at ASC
            """, (ticket_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def add_comment(ticket_id, user_id, comment_text):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO ticket_comments (ticket_id, user_id, comment) VALUES (%s, %s, %s)",
                (ticket_id, user_id, comment_text)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_status(ticket_id, status):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE tickets SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, ticket_id)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_overdue_tickets():
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # ✅ FIXED: MySQL uses INTERVAL 48 HOUR (not '48 hours')
            cur.execute("""
                SELECT t.id as ticket_id, t.title, u.email as admin_email, u.full_name as admin_name
                FROM tickets t
                JOIN users u ON t.society_id = u.society_id
                WHERE t.status = 'open' AND u.role = 'admin'
                  AND t.created_at < NOW() - INTERVAL 48 HOUR
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(ticket_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM ticket_comments WHERE ticket_id = %s", (ticket_id,))
            cur.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()