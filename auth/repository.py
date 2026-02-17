from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class AuthRepository:
    """
    Handles authentication-related database operations.
    """
    
    # auth/repository.py

    @staticmethod
    def get_user_by_email(email):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Using 'full_name' exactly as it appears in your CREATE TABLE users script
        cur.execute("""
            SELECT 
                id, 
                email, 
                password_hash, 
                full_name, 
                role, 
                society_id, 
                is_active
            FROM users
            WHERE email = %s 
              AND is_active = TRUE
        """, (email,))

        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    



class UserRepository:
    """
    Handles general user management (Owners, Tenants, etc.)
    """

    @staticmethod
    def get_users_by_society_and_roles(society_id, roles):
        """
        Fetch users belonging to a specific society with specific roles.
        'roles' should be a tuple, e.g., ('owner', 'tenant')
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT id, full_name, email, role 
            FROM users 
            WHERE society_id = %s 
            AND role IN %s
            ORDER BY full_name
        """
        cur.execute(query, (society_id, roles))
        
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users

    @staticmethod
    def get_users_by_society_and_role(society_id, role):
        """
        Backward compatibility wrapper for a single role.
        """
        return UserRepository.get_users_by_society_and_roles(
            society_id=society_id,
            roles=(role,)
        )

    @staticmethod
    def create_user(data):
        """
        Inserts a new user (Owner/Tenant) into the database.
        """
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (
                full_name,
                email,
                password_hash,
                role,
                society_id,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """,
            (
                data["full_name"],
                data["email"],
                data["password_hash"],
                data["role"],
                data["society_id"],
            )
        )

        conn.commit()
        cur.close()
        conn.close()
        return True
    

    # @staticmethod
    # def get_by_email(email):
    #     conn = get_db_connection()
    #     cur = conn.cursor(cursor_factory=RealDictCursor)
    #     # Fetching from the unified 'users' table
    #     cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    #     user = cur.fetchone()
    #     cur.close()
    #     conn.close()
    #     return user




    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_password(user_id, new_password_hash):
        """Updates the password in the database."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_password_hash, user_id))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()


    @staticmethod
    def update_password_by_email(email, new_password_hash):
        """
        FIXES: AttributeError: type object 'UserRepository' has no attribute 'update_password_by_email'
        """
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Case-insensitive update
            cur.execute("""
                UPDATE users 
                SET password_hash = %s 
                WHERE LOWER(email) = LOWER(%s)
            """, (new_password_hash, email))
            conn.commit()
            # Returns True if a user was actually found and updated
            return cur.rowcount > 0 
        finally:
            cur.close()
            conn.close()