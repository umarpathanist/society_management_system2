from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class TicketRepository:

    # ======================================================
    # 1. CREATE TICKET (FIXED: Handles ID safely)
    # ======================================================
    # tickets/repository.py

    @staticmethod
    def create(data):
        """
        Inserts a new ticket. 
        FIXED: Robust ID extraction to stop 'Error 0'.
        """
        conn = get_db_connection()
        # We request a standard cursor to be as safe as possible
        cur = conn.cursor() 
        try:
            cur.execute("""
                INSERT INTO tickets (user_id, society_id, title, description, category, priority)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                data['user_id'], 
                data['society_id'], 
                data['title'], 
                data['description'], 
                data['category'], 
                data['priority']
            ))
            
            result = cur.fetchone()
            if result:
                # --- BULLETPROOF ID EXTRACTION ---
                # If it's a dict, get 'id'. If it's a tuple/list, get index 0.
                if isinstance(result, dict):
                    new_id = result.get('id')
                else:
                    new_id = result[0]
                
                conn.commit()
                return new_id
            return None
        except Exception as e:
            conn.rollback()
            # Log the full error to your terminal for debugging
            print(f"DATABASE ERROR: {e}")
            raise e
        finally:
            cur.close()
            conn.close()

    # ======================================================
    # 2. FETCHING METHODS
    # ======================================================
    @staticmethod
    def get_by_id(ticket_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT t.*, u.full_name as creator_name, u.email as owner_email
                FROM tickets t 
                JOIN users u ON t.user_id = u.id 
                WHERE t.id = %s
            """, (ticket_id,))
            return cur.fetchone()
        finally:
            cur.close(); conn.close()

    @staticmethod
    def get_by_society(society_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT t.*, u.full_name as creator_name 
                FROM tickets t JOIN users u ON t.user_id = u.id 
                WHERE t.society_id = %s ORDER BY t.created_at DESC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM tickets WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    # ======================================================
    # 3. COMMENTS & STATUS (Lifecycle)
    # ======================================================
    @staticmethod
    def get_comments(ticket_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT tc.*, u.full_name as user_name 
                FROM ticket_comments tc 
                JOIN users u ON tc.user_id = u.id 
                WHERE tc.ticket_id = %s ORDER BY tc.created_at ASC
            """, (ticket_id,))
            return cur.fetchall()
        finally:
            cur.close(); conn.close()

    @staticmethod
    def add_comment(ticket_id, user_id, comment_text):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO ticket_comments (ticket_id, user_id, comment) VALUES (%s, %s, %s)", 
                        (ticket_id, user_id, comment_text))
            conn.commit()
        finally: cur.close(); conn.close()

    @staticmethod
    def update_status(ticket_id, status):
        conn = get_db_connection(); cur = conn.cursor()
        try:
            cur.execute("UPDATE tickets SET status = %s, updated_at = NOW() WHERE id = %s", (status, ticket_id))
            conn.commit()
        finally: cur.close(); conn.close()

    # ======================================================
    # 4. SLA ESCALATION
    # ======================================================
    @staticmethod
    def get_overdue_tickets():
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT t.id as ticket_id, t.title, u.email as admin_email, u.full_name as admin_name
                FROM tickets t
                JOIN users u ON t.society_id = u.society_id
                WHERE t.status = 'open' AND u.role = 'admin'
                  AND t.created_at < NOW() - INTERVAL '48 hours'
            """)
            return cur.fetchall()
        finally: cur.close(); conn.close()


        # Inside TicketRepository class in tickets/repository.py

    @staticmethod
    def delete(ticket_id):
        """Removes a ticket and its associated comments from the database."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # We delete the ticket; ticket_comments will be removed automatically 
            # if ON DELETE CASCADE is set, otherwise delete comments first.
            cur.execute("DELETE FROM ticket_comments WHERE ticket_id = %s", (ticket_id,))
            cur.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close(); conn.close()
