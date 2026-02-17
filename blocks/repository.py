# from database.connection import  get_db_connection
# from psycopg2.extras import RealDictCursor
# import psycopg2


# class BlockRepository:

#     @staticmethod
#     def create(data):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         cur.execute("""
#             INSERT INTO blocks (name, society_id)
#             VALUES (%s, %s)
#             RETURNING id
#         """, (
#             data["name"],
#             data["society_id"]
#         ))

#         row = cur.fetchone()
#         block_id = row["id"]

#         conn.commit()
#         cur.close()
#         conn.close()

#         return block_id


#     @staticmethod
#     def get_by_id(block_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("SELECT * FROM blocks WHERE id = %s", (block_id,))
#         row = cur.fetchone()
#         cur.close()
#         conn.close()
#         return row


#     @staticmethod
#     def update(block_id, data):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("""
#             UPDATE blocks
#             SET name=%s, floors=%s
#             WHERE id=%s
#         """, (data.get("name"), data.get("floors"), block_id))
#         conn.commit()
#         cur.close()
#         conn.close()


#     @staticmethod
#     def delete(block_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("DELETE FROM blocks WHERE id=%s", (block_id,))
#         conn.commit()
#         cur.close()
#         conn.close()


#     @staticmethod
#     def get_blocks_by_society(society_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         cur.execute("""
#             SELECT 
#                 b.id,
#                 b.name,
#                 b.created_at,
#                 COUNT(f.id) AS total_flats
#             FROM blocks b
#             LEFT JOIN flats f ON f.block_id = b.id
#             WHERE b.society_id = %s
#             GROUP BY b.id
#             ORDER BY b.id
#         """, (society_id,))

#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows

#     # blocks/repository.py

#     @staticmethod
#     def get_by_society(society_id):
#         """
#         Fetches blocks for a society. 
#         Uses society's default if block-specific count is missing.
#         """
#         conn = get_db_connection()
#         from psycopg2.extras import RealDictCursor
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT 
#                     b.id, 
#                     b.name, 
#                     b.society_id,
#                     -- We name this 'floors' to match the HTML variable {{ b.floors }}
#                     COALESCE(b.floors, s.floors_per_block, 0) as floors
#                 FROM blocks b
#                 JOIN societies s ON b.society_id = s.id
#                 WHERE b.society_id = %s 
#                 ORDER BY b.id DESC
#             """, (society_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()
            
#     @staticmethod
#     def get_by_id(block_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT * FROM blocks WHERE id = %s", (block_id,))
#             return cur.fetchone()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def update(block_id, name, floors):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("""
#                 UPDATE blocks SET name = %s, floors = %s 
#                 WHERE id = %s
#             """, (name, floors, block_id))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def delete(block_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             # Note: This will delete all flats in this block due to CASCADE
#             cur.execute("DELETE FROM blocks WHERE id = %s", (block_id,))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()





# blocks/repository.py
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

# blocks/repository.py
from database.connection import get_db_connection

class BlockRepository:
    @staticmethod
    def create(society_id, name, floors):
        """Inserts a block and returns ID safely handling different cursor types."""
        conn = get_db_connection()
        cur = conn.cursor() 
        try:
            cur.execute("""
                INSERT INTO blocks (society_id, name, floors)
                VALUES (%s, %s, %s) RETURNING id
            """, (society_id, name, floors))
            
            result = cur.fetchone()
            if result:
                # SAFE CHECK: Works for {'id': 1} or (1,)
                new_id = result.get('id') if isinstance(result, dict) else result[0]
                conn.commit()
                return new_id
            return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    # ... keep your get_by_society and other methods below ...
    #     
    # blocks/repository.py

    @staticmethod
    def get_by_society(society_id):
        """
        Fetches blocks for a society. 
        Uses society's default if block-specific count is missing.
        UPDATED: Sorted in Ascending order (A, B, C...)
        """
        conn = get_db_connection()
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
                -- CHANGE THIS LINE: Order by name instead of ID
                ORDER BY b.name ASC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
            
    @staticmethod
    def get_by_id(block_id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
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
            cur.execute("UPDATE blocks SET name = %s, floors = %s WHERE id = %s", (name, floors, block_id))
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