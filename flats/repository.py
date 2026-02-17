# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor

# class FlatRepository:

#     @staticmethod
#     def get_by_block(block_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("""
#             SELECT f.id, f.flat_number, f.floor_number, f.is_occupied, f.owner_id, f.tenant_id
#             FROM flats f
#             WHERE f.block_id = %s
#             ORDER BY f.floor_number, f.flat_number
#         """, (block_id,))
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows

#     @staticmethod
#     def create(data):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("""
#             INSERT INTO flats (block_id, flat_number, floor_number, is_occupied)
#             VALUES (%s, %s, %s, FALSE)
#         """, (data["block_id"], data["flat_number"], data["floor_number"]))
#         conn.commit()
#         cur.close()
#         conn.close()

#     @staticmethod
#     def get_by_id(flat_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         cur.execute("""
#             SELECT f.*, b.society_id
#             FROM flats f
#             JOIN blocks b ON b.id = f.block_id
#             WHERE f.id = %s
#         """, (flat_id,))
#         flat = cur.fetchone()
#         cur.close()
#         conn.close()
#         return flat

#     @staticmethod
#     def toggle_status(flat_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("UPDATE flats SET is_occupied = NOT is_occupied WHERE id = %s", (flat_id,))
#         conn.commit()
#         cur.close()
#         conn.close()

#     @staticmethod
#     def clear_assignment(flat_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("""
#             UPDATE flats
#             SET owner_id = NULL, tenant_id = NULL, is_occupied = FALSE
#             WHERE id = %s
#         """, (flat_id,))
#         conn.commit()
#         cur.close()
#         conn.close()

#     # flats/repository.py

#     @staticmethod
#     def assign_user(flat_id, user_id, role):
#         """Unified method to assign either an owner or a tenant and mark as occupied."""
#         conn = get_db_connection()
#         cur = conn.cursor()
        
#         if role == "owner":
#             # Added is_occupied = TRUE here
#             cur.execute("""
#                 UPDATE flats 
#                 SET owner_id = %s, is_occupied = TRUE 
#                 WHERE id = %s
#             """, (user_id, flat_id))
#         elif role == "tenant":
#             cur.execute("""
#                 UPDATE flats 
#                 SET tenant_id = %s, is_occupied = TRUE 
#                 WHERE id = %s
#             """, (user_id, flat_id))
            
#         conn.commit()
#         cur.close()
#         conn.close()

#     # Also update these if your service still calls them specifically:
#     @staticmethod
#     def assign_owner(flat_id, user_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("""
#             UPDATE flats 
#             SET owner_id = %s, is_occupied = TRUE 
#             WHERE id = %s
#         """, (user_id, flat_id))
#         conn.commit()
#         cur.close()
#         conn.close()

#     @staticmethod
#     def assign_tenant(flat_id, user_id):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("""
#             UPDATE flats 
#             SET tenant_id = %s, is_occupied = TRUE 
#             WHERE id = %s
#         """, (user_id, flat_id))
#         conn.commit()
#         cur.close()
#         conn.close()
        
        
#     @staticmethod
#     def get_by_block(block_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         cur.execute("""
#             SELECT 
#                 f.id, 
#                 f.flat_number, 
#                 f.floor_number, 
#                 f.is_occupied, 
#                 f.owner_id, 
#                 f.tenant_id,
#                 o.full_name AS owner_name,
#                 t.full_name AS tenant_name
#             FROM flats f
#             LEFT JOIN users o ON f.owner_id = o.id
#             LEFT JOIN users t ON f.tenant_id = t.id
#             WHERE f.block_id = %s
#             ORDER BY f.floor_number, f.flat_number
#         """, (block_id,))

#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows
    
    

#     @staticmethod
#     def unassign_user(flat_id, role):
#         conn = get_db_connection()
#         cur = conn.cursor()
        
#         # Decide which column to clear
#         column = "owner_id" if role == "owner" else "tenant_id"
        
#         try:
#             cur.execute(f"UPDATE flats SET {column} = NULL WHERE id = %s", (flat_id,))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()


#     # flats/repository.py
#     # def get_all_by_society(society_id):
#         """
#         Fetches all flats belonging to a specific society.
#         Required for bulk maintenance generation.
#         """
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT f.id 
#                 FROM flats f
#                 JOIN blocks b ON f.block_id = b.id
#                 WHERE b.society_id = %s
#             """, (society_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()

#     # flats/repository.py

#         # flats/repository.py

#     # @staticmethod
#     # def get_all_by_society(society_id):
#     #     """
#     #     CRITICAL FIX: This must fetch flat_number and block_id 
#     #     for the dynamic dropdown to work.
#     #     """
#     #     conn = get_db_connection()
#     #     from psycopg2.extras import RealDictCursor
#     #     cur = conn.cursor(cursor_factory=RealDictCursor)
#     #     try:
#     #         cur.execute("""
#     #             SELECT f.id, f.flat_number, f.block_id 
#     #             FROM flats f
#     #             JOIN blocks b ON f.block_id = b.id
#     #             WHERE b.society_id = %s
#     #             ORDER BY f.flat_number
#     #         """, (society_id,))
#     #         rows = cur.fetchall()
#     #         # Debug: check your console to see if flats are actually found
#     #         print(f"DATABASE LOG: Found {len(rows)} flats for society {society_id}")
#     #         return rows
#     #     finally:
#     #         cur.close()
#     #         conn.close()

#     # @staticmethod
#     # def get_by_block(block_id):
#     #     """Fetches all flats for a specific block with owner/tenant details."""
#     #     conn = get_db_connection()
#     #     cur = conn.cursor(cursor_factory=RealDictCursor)
#     #     try:
#     #         # We use LEFT JOIN so flats appear even if they are VACANT
#     #         cur.execute("""
#     #             SELECT 
#     #                 f.id, f.flat_number, f.floor_number, f.is_occupied,
#     #                 uo.full_name as owner_name, 
#     #                 ut.full_name as tenant_name
#     #             FROM flats f
#     #             LEFT JOIN users uo ON f.owner_id = uo.id
#     #             LEFT JOIN users ut ON f.tenant_id = ut.id
#     #             WHERE f.block_id = %s
#     #             ORDER BY f.floor_number, f.flat_number
#     #         """, (block_id,))
#     #         return cur.fetchall()
#     #     finally:
#     #         cur.close()
#     #         conn.close()

# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor

# class FlatRepository:

#     @staticmethod
#     def get_all_by_society(society_id):
#         """
#         Fetches all flats for a society, sorted by floor then flat number.
#         This ensures A-101 comes before A-1201.
#         """
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT f.id, f.flat_number, f.block_id, f.floor_number 
#                 FROM flats f
#                 JOIN blocks b ON f.block_id = b.id
#                 WHERE b.society_id = %s
#                 -- Primary Sort: Floor (1, 2, ... 12)
#                 -- Secondary Sort: Flat Number (101, 102...)
#                 ORDER BY f.floor_number ASC, f.flat_number ASC
#             """, (society_id,))
#             rows = cur.fetchall()
#             print(f"DATABASE LOG: Found {len(rows)} flats for society {society_id}")
#             return rows
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_by_block(block_id):
#         """
#         Fetches all flats for a specific block with owner/tenant details, 
#         sorted in architectural order (Floor 1 to Floor 12).
#         """
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT 
#                     f.id, f.flat_number, f.floor_number, f.is_occupied, f.owner_id, f.tenant_id,
#                     uo.full_name as owner_name, 
#                     ut.full_name as tenant_name
#                 FROM flats f
#                 LEFT JOIN users uo ON f.owner_id = uo.id
#                 LEFT JOIN users ut ON f.tenant_id = ut.id
#                 WHERE f.block_id = %s
#                 -- Ensures numerical floor order regardless of string length
#                 ORDER BY f.floor_number ASC, f.flat_number ASC
#             """, (block_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()

#     # ... keep any other methods (assign_user, create_multiple, etc.) exactly as they were
    
#     @staticmethod
#     def create_multiple(flats_list):
#         """Batch inserts flats and commits them to the database."""
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             query = """
#                 INSERT INTO flats (block_id, flat_number, floor_number, is_occupied)
#                 VALUES (%s, %s, %s, FALSE)
#             """
#             for f in flats_list:
#                 cur.execute(query, (f['block_id'], f['flat_number'], f['floor_number']))
#             conn.commit() # This makes the flats permanent
#             return True
#         except Exception as e:
#             conn.rollback()
#             raise e
#         finally:
#             cur.close()
#             conn.close()


#     @staticmethod
#     def get_occupied_by_society(society_id):
#         """
#         Fetches only the IDs of flats that are currently occupied in a society.
#         """
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT f.id 
#                 FROM flats f
#                 JOIN blocks b ON f.block_id = b.id
#                 WHERE b.society_id = %s AND f.is_occupied = TRUE
#             """, (society_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()

#     # flats/repository.py

# # flats/repository.py

#     @staticmethod
#     def get_occupied_with_maintenance(block_id):
#         """
#         Fetches flats that are:
#         1. Occupied = TRUE
#         2. Belong to the selected block
#         3. Have at least one record in the maintenance table
#         """
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("""
#                 SELECT DISTINCT f.id, f.flat_number 
#                 FROM flats f
#                 JOIN maintenance m ON f.id = m.flat_id
#                 WHERE f.block_id = %s 
#                 AND f.is_occupied = TRUE
#                 ORDER BY f.flat_number ASC
#             """, (block_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()



from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class FlatRepository:

    # ======================================================
    # 1. GET BY ID (FIXES: AttributeError)
    # ======================================================
    @staticmethod
    def get_by_id(flat_id):
        """Fetches a single flat record with society context."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT f.*, b.society_id
                FROM flats f
                JOIN blocks b ON b.id = f.block_id
                WHERE f.id = %s
            """, (flat_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    # ======================================================
    # 2. LISTING & SEARCHING
    # ======================================================
    @staticmethod
    def get_by_block(block_id):
        """Fetches flats for a block in floor-wise order (1, 2, 3...)."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT f.*, uo.full_name as owner_name, ut.full_name as tenant_name
                FROM flats f
                LEFT JOIN users uo ON f.owner_id = uo.id
                LEFT JOIN users ut ON f.tenant_id = ut.id
                WHERE f.block_id = %s
                ORDER BY f.floor_number ASC, f.flat_number ASC
            """, (block_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_occupied_by_society(society_id):
        """Used for automated billing."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT f.id FROM flats f
                JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s AND f.is_occupied = TRUE
            """, (society_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_occupied_with_maintenance(block_id):
        """Used for manual payment dropdown."""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT DISTINCT f.id, f.flat_number 
                FROM flats f
                JOIN maintenance m ON f.id = m.flat_id
                WHERE f.block_id = %s AND f.is_occupied = TRUE
                ORDER BY f.flat_number ASC
            """, (block_id,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    # ======================================================
    # 3. UPDATING & ASSIGNING
    # ======================================================
    @staticmethod
    def assign_user(flat_id, user_id, role):
        """Links user to flat and marks as occupied."""
        conn = get_db_connection()
        cur = conn.cursor()
        column = "owner_id" if role == "owner" else "tenant_id"
        try:
            cur.execute(f"UPDATE flats SET {column} = %s, is_occupied = TRUE WHERE id = %s", (user_id, flat_id))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def unassign_user(flat_id, role):
        """Removes user from flat."""
        conn = get_db_connection()
        cur = conn.cursor()
        column = "owner_id" if role == "owner" else "tenant_id"
        try:
            cur.execute(f"UPDATE flats SET {column} = NULL WHERE id = %s", (flat_id,))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def create_multiple(flats_list):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            query = "INSERT INTO flats (block_id, flat_number, floor_number) VALUES (%s, %s, %s)"
            for f in flats_list:
                cur.execute(query, (f['block_id'], f['flat_number'], f['floor_number']))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()