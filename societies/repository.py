from database.connection import get_db_connection
from blocks.repository import BlockRepository
from flats.repository import FlatRepository

class SocietyRepository:

    @staticmethod
    def get_all():
        """Fetches all societies sorted by Name (A-Z)."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 
                    s.id, s.name, s.address,
                    (SELECT COUNT(*) FROM blocks b WHERE b.society_id = s.id) as blocks,
                    (SELECT COUNT(*) FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = s.id) as flats,
                    (SELECT full_name FROM users WHERE society_id = s.id AND role = 'treasurer' LIMIT 1) as treasurer_name
                FROM societies s 
                ORDER BY s.name ASC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_by_admin(society_id):
        """Fetches society for Admin view."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 
                    s.id, s.name, s.address,
                    (SELECT COUNT(*) FROM blocks b WHERE b.society_id = s.id) as blocks,
                    (SELECT COUNT(*) FROM flats f JOIN blocks b ON f.block_id = b.id WHERE b.society_id = s.id) as flats,
                    (SELECT full_name FROM users WHERE society_id = s.id AND role = 'treasurer' LIMIT 1) as treasurer_name
                FROM societies s 
                WHERE s.id = %s
                ORDER BY s.name ASC
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def create(data):
        """Creates society and auto-generates blocks and flats."""
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # ✅ FIXED: Removed RETURNING id, using lastrowid instead
            cur.execute("""
                INSERT INTO societies (name, address, total_blocks, floors_per_block, flats_per_floor)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['name'], data['address'], data['total_blocks'], data['floors_per_block'], data['flats_per_floor']))
            
            society_id = cur.lastrowid  # ✅ MySQL way to get inserted ID
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
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Update society info
            cur.execute("""
                UPDATE societies 
                SET name=%s, address=%s, total_blocks=%s, floors_per_block=%s, flats_per_floor=%s
                WHERE id=%s
            """, (data['name'], data['address'], data['total_blocks'], 
                  data['floors_per_block'], data['flats_per_floor'], society_id))

            # ✅ Update blocks floors
            cur.execute("""
                UPDATE blocks SET floors=%s WHERE society_id=%s
            """, (data['floors_per_block'], society_id))

            conn.commit()

            # ✅ Now regenerate missing flats for each block
            f_qty = int(data['floors_per_block'])
            fl_pf = int(data['flats_per_floor'])

            cur2 = conn.cursor()
            cur2.execute("SELECT id, name FROM blocks WHERE society_id=%s", (society_id,))
            blocks = cur2.fetchall()

            for block in blocks:
                block_id = block['id']
                block_label = block['name'].replace("Block ", "")

                for floor in range(1, f_qty + 1):
                    for j in range(1, fl_pf + 1):
                        flat_number = f"{block_label}-{floor}{j:02d}"

                        # Only insert if flat doesn't exist already
                        cur2.execute("""
                            SELECT id FROM flats 
                            WHERE block_id=%s AND flat_number=%s
                        """, (block_id, flat_number))

                        exists = cur2.fetchone()
                        if not exists:
                            cur2.execute("""
                                INSERT INTO flats (block_id, flat_number, floor_number)
                                VALUES (%s, %s, %s)
                            """, (block_id, flat_number, floor))

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
        cur = conn.cursor()
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
