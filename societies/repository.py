
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from blocks.repository import BlockRepository
from flats.repository import FlatRepository

class SocietyRepository:

    # @staticmethod
    # def get_all():
    #     """Fetches all societies for the Super Admin view."""
    #     conn = get_db_connection()
    #     cur = conn.cursor(cursor_factory=RealDictCursor)
    #     try:
    #         cur.execute("""
    #             SELECT 
    #                 s.id, s.name, s.address,
    #                 (SELECT COUNT(*) FROM blocks b WHERE b.society_id = s.id) as blocks,
    #                 (SELECT COUNT(*) FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = s.id) as flats,
    #                 (SELECT full_name FROM users WHERE society_id = s.id AND role = 'treasurer' LIMIT 1) as treasurer_name
    #             FROM societies s ORDER BY s.id DESC
    #         """)
    #         return cur.fetchall()
    #     finally:
    #         cur.close()
    #         conn.close()

    # @staticmethod
    # def get_by_admin(society_id):
    #     """
    #     FIXES: AttributeError: no attribute 'get_by_admin'
    #     Fetches the specific society assigned to an Admin.
    #     """
    #     conn = get_db_connection()
    #     cur = conn.cursor(cursor_factory=RealDictCursor)
    #     try:
    #         cur.execute("""
    #             SELECT 
    #                 s.id, s.name, s.address,
    #                 (SELECT COUNT(*) FROM blocks b WHERE b.society_id = s.id) as blocks,
    #                 (SELECT COUNT(*) FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = s.id) as flats,
    #                 (SELECT full_name FROM users WHERE society_id = s.id AND role = 'treasurer' LIMIT 1) as treasurer_name
    #             FROM societies s 
    #             WHERE s.id = %s
    #         """, (society_id,))
    #         # Return as a list so the HTML loop works
    #         return cur.fetchall()
    #     finally:
    #         cur.close()
    #         conn.close()

    from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class SocietyRepository:

    # ======================================================
    # 1. GET ALL SOCIETIES (Sorted Alphabetically)
    # ======================================================
    @staticmethod
    def get_all():
        """Fetches all societies sorted by Name (A-Z)."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    s.id, s.name, s.address,
                    (SELECT COUNT(*) FROM blocks b WHERE b.society_id = s.id) as blocks,
                    (SELECT COUNT(*) FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = s.id) as flats,
                    (SELECT full_name FROM users WHERE society_id = s.id AND role = 'treasurer' LIMIT 1) as treasurer_name
                FROM societies s 
                ORDER BY s.name ASC  -- Changed from s.id DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    # ======================================================
    # 2. GET BY ADMIN (Sorted Alphabetically)
    # ======================================================
    @staticmethod
    def get_by_admin(society_id):
        """Fetches society for Admin view, sorted by Name."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT 
                    s.id, s.name, s.address,
                    (SELECT COUNT(*) FROM blocks b WHERE b.society_id = s.id) as blocks,
                    (SELECT COUNT(*) FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = s.id) as flats,
                    (SELECT full_name FROM users WHERE society_id = s.id AND role = 'treasurer' LIMIT 1) as treasurer_name
                FROM societies s 
                WHERE s.id = %s
                ORDER BY s.name ASC -- Ensure alphabetical order
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    # ... rest of your repository methods (create, update, delete, get_by_id) ...

    @staticmethod
    def create(data):
        """Creates society and auto-generates blocks and flats."""
        conn = get_db_connection()
        cur = conn.cursor() 
        try:
            cur.execute("""
                INSERT INTO societies (name, address, total_blocks, floors_per_block, flats_per_floor)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (data['name'], data['address'], data['total_blocks'], data['floors_per_block'], data['flats_per_floor']))
            
            res = cur.fetchone()
            society_id = res['id'] if isinstance(res, dict) else res[0]
            conn.commit()

            # Infrastructure loop
            b_qty = int(data['total_blocks'])
            f_qty = int(data['floors_per_block'])
            fl_pf = int(data['flats_per_floor'])

            for i in range(1, b_qty + 1):
                label = chr(64 + i) 
                block_id = BlockRepository.create(society_id, f"Block {label}", f_qty)
                
                new_flats = []
                for floor in range(1, f_qty + 1):
                    for j in range(1, fl_pf + 1):
                        new_flats.append({
                            "block_id": block_id,
                            "flat_number": f"{label}-{floor}{j:02d}",
                            "floor_number": floor
                        })
                if new_flats:
                    FlatRepository.create_multiple(new_flats)

            return society_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update(society_id, data):
        """Updates basic info and generates flats if society is empty."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE societies 
                SET name=%s, address=%s, total_blocks=%s, floors_per_block=%s, flats_per_floor=%s
                WHERE id=%s
            """, (data['name'], data['address'], data['total_blocks'], 
                  data['floors_per_block'], data['flats_per_floor'], society_id))

            cur.execute("SELECT COUNT(*) FROM blocks WHERE society_id = %s", (society_id,))
            count_res = cur.fetchone()
            existing_blocks = count_res['count'] if isinstance(count_res, dict) else count_res[0]

            if existing_blocks == 0:
                # Same logic as create
                b_qty, f_qty, fl_pf = int(data['total_blocks']), int(data['floors_per_block']), int(data['flats_per_floor'])
                for i in range(1, b_qty + 1):
                    lbl = chr(64 + i)
                    bid = BlockRepository.create(society_id, f"Block {lbl}", f_qty)
                    flts = []
                    for f in range(1, f_qty + 1):
                        for j in range(1, fl_pf + 1):
                            flts.append({"block_id": bid, "flat_number": f"{lbl}-{f}{j:02d}", "floor_number": f})
                    FlatRepository.create_multiple(flts)

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_id(id):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM societies WHERE id = %s", (id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def delete(id):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM societies WHERE id = %s", (id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()