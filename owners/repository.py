from database.connection import get_db_connection

class OwnerRepository:

    @staticmethod
    def create_user(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role, society_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data["full_name"], data["email"], data["password_hash"],
                data["role"].lower(), data["society_id"]
            ))
            new_id = cur.lastrowid 
            conn.commit()
            # Return same structure as before
            return {
                "id": new_id,
                "full_name": data["full_name"],
                "email": data["email"],
                "role": data["role"].lower()
            }
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_users_by_society_and_roles(society_id, roles):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            placeholders = ', '.join(['%s'] * len(roles))
            query = f"SELECT id, full_name, email, role FROM users WHERE LOWER(role) IN ({placeholders})"
            params = [r.lower() for r in roles]

            if society_id:
                query += " AND society_id = %s"
                params.append(society_id)

            query += " ORDER BY full_name ASC"
            cur.execute(query, params)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_flats_by_user(user_id, role):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = """
                SELECT f.id, f.flat_number, b.name AS block_name, s.name AS society_name
                FROM flats f
                JOIN blocks b ON f.block_id = b.id
                JOIN societies s ON b.society_id = s.id
                WHERE """
            query += "f.owner_id = %s" if role.lower() == 'owner' else "f.tenant_id = %s"
            cur.execute(query, (user_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM users WHERE id = %s AND role IN ('owner', 'tenant')",
                (user_id,)
            )
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
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()