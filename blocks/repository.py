from database.connection import get_db_connection

class BlockRepository:

    @staticmethod
    def create(society_id, name, floors):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # ✅ FIXED: Removed RETURNING id, using lastrowid
            cur.execute("""
                INSERT INTO blocks (society_id, name, floors)
                VALUES (%s, %s, %s)
            """, (society_id, name, floors))

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
    def get_by_society(society_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 
                    b.id, 
                    b.name, 
                    b.society_id,
                    COALESCE(b.floors, s.floors_per_block, 0) as floors
                FROM blocks b
                JOIN societies s ON b.society_id = s.id
                WHERE b.society_id = %s 
                ORDER BY b.name ASC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(block_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM blocks WHERE id = %s", (block_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update(block_id, name, floors):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE blocks SET name = %s, floors = %s WHERE id = %s",
                (name, floors, block_id)
            )
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(block_id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM blocks WHERE id = %s", (block_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()