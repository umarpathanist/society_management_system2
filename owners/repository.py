# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor

# class OwnerRepository:
#     @staticmethod
#     def create_user(data):
#         """Creates a user in the users table and returns the new user object."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 INSERT INTO users (full_name, email, password_hash, role, society_id)
#                 VALUES (%s, %s, %s, %s, %s)
#                 RETURNING id, full_name, email, role
#             """, (
#                 data["full_name"],
#                 data["email"],
#                 data["password_hash"],
#                 data["role"].lower(),  # Standardize to lowercase
#                 data["society_id"]
#             ))
#             user = cur.fetchone()
#             conn.commit()
#             return user
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_users_by_society_and_roles(society_id, roles):
#         """Fetches users based on roles (owner/tenant) and society filter."""
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
        
#         query = "SELECT id, full_name, email, role FROM users WHERE role = ANY(%s)"
#         params = [list(roles)]

#         if society_id:
#             query += " AND society_id = %s"
#             params.append(society_id)
            
#         query += " ORDER BY full_name"
        
#         cur.execute(query, params)
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows

#     # owners/repository.py

#     @staticmethod
#     def get_flats_by_user(user_id, role):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
        
#         # We join blocks and societies to get the names for display
#         query = """
#             SELECT f.id, f.flat_number, b.name AS block_name, s.name AS society_name
#             FROM flats f
#             JOIN blocks b ON f.block_id = b.id
#             JOIN societies s ON b.society_id = s.id
#             WHERE """
        
#         if role.lower() == 'owner':
#             query += "f.owner_id = %s"
#         else:
#             query += "f.tenant_id = %s"
            
#         cur.execute(query, (user_id,))
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows





from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class OwnerRepository:
    @staticmethod
    def create_user(data):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role, society_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, full_name, email, role
            """, (data["full_name"], data["email"], data["password_hash"], data["role"].lower(), data["society_id"]))
            user = cur.fetchone()
            conn.commit()
            return user
        finally:
            cur.close()
            conn.close()

    # @staticmethod
    # def get_users_by_society_and_roles(society_id, roles):
    #     conn = get_db_connection()
    #     cur = conn.cursor(cursor_factory=RealDictCursor)
    #     query = "SELECT id, full_name, email, role FROM users WHERE role = ANY(%s)"
    #     params = [list(roles)]
    #     if society_id:
    #         query += " AND society_id = %s"
    #         params.append(society_id)
    #     query += " ORDER BY full_name"
    #     cur.execute(query, params)
    #     rows = cur.fetchall()
    #     cur.close()
    #     conn.close()
    #     return rows

    # owners/repository.py

    @staticmethod
    def get_users_by_society_and_roles(society_id, roles):
        """Fetches users based on roles. Case-insensitive and handles Super Admin views."""
        conn = get_db_connection()
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # 1. Base Query - Fetching owners/tenants regardless of capitalization
            # Use tuple(roles) for the IN clause
            query = "SELECT id, full_name, email, role FROM users WHERE LOWER(role) IN %s"
            params = [tuple(r.lower() for r in roles)]

            # 2. Filter by society ONLY if one is provided (Admins)
            # If society_id is None, this block is skipped (Super Admin)
            if society_id:
                query += " AND society_id = %s"
                params.append(society_id)
                
            query += " ORDER BY full_name ASC"
            
            cur.execute(query, tuple(params))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

            
    @staticmethod
    def get_flats_by_user(user_id, role):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT f.id, f.flat_number, b.name AS block_name, s.name AS society_name
            FROM flats f
            JOIN blocks b ON f.block_id = b.id
            JOIN societies s ON b.society_id = s.id
            WHERE """
        query += "f.owner_id = %s" if role.lower() == 'owner' else "f.tenant_id = %s"
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

# owners/repository.py


    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM users WHERE id = %s AND role IN ('owner', 'tenant')", (user_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update(user_id, data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users 
                SET full_name = %s, email = %s, role = %s
                WHERE id = %s
            """, (data['full_name'], data['email'], data['role'].lower(), user_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Note: Flat assignments (owner_id/tenant_id) will be set to NULL automatically 
            # if your DB has 'ON DELETE SET NULL' configured.
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()