# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor

# class IncomeRepository:
#     @staticmethod
#     def add(data):
#         conn = get_db_connection()
#         cur = conn.cursor()
#         try:
#             cur.execute("""
#                 INSERT INTO other_income (society_id, source_name, amount, income_date, description)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (
#                 data['society_id'], 
#                 data['source_name'], 
#                 data['amount'], 
#                 data['income_date'], 
#                 data['description']
#             ))
#             conn.commit()
#         finally:
#             cur.close()
#             conn.close()

#     @staticmethod
#     def get_by_society(society_id):
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         try:
#             cur.execute("SELECT * FROM other_income WHERE society_id = %s ORDER BY income_date DESC", (society_id,))
#             return cur.fetchall()
#         finally:
#             cur.close()
#             conn.close()





# income/repository.py
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor

class IncomeRepository:
    # Method for adding miscellaneous income stays the same...
    @staticmethod
    def add(data):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO other_income (society_id, source_name, amount, income_date, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['society_id'], data['source_name'], data['amount'], data['income_date'], data['description']))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    # @staticmethod
    # def get_by_society(society_id):
    #     """
    #     FETCHES COMBINED INCOME:
    #     1. Miscellaneous Income (Other Income table)
    #     2. Maintenance Payments (Maintenance table where status is paid)
    #     """
    #     conn = get_db_connection()
    #     cur = conn.cursor(cursor_factory=RealDictCursor)
    #     try:
    #         cur.execute("""
    #             -- Part A: Get Misc Income
    #             SELECT 
    #                 source_name as source, 
    #                 amount, 
    #                 income_date as date, 
    #                 COALESCE(description, '-') as info,
    #                 'Misc' as type
    #             FROM other_income 
    #             WHERE society_id = %s

    #             UNION ALL

    #             -- Part B: Get Maintenance Payments
    #             SELECT 
    #                 'Maintenance: ' || f.flat_number as source, 
    #                 m.amount, 
    #                 m.due_date as date, -- Use due_date or created_at
    #                 m.month || ' ' || m.year as info,
    #                 'Maint' as type
    #             FROM maintenance m
    #             JOIN flats f ON m.flat_id = f.id
    #             JOIN blocks b ON f.block_id = b.id
    #             WHERE b.society_id = %s AND m.status = 'paid'

    #             ORDER BY date DESC
    #         """, (society_id, society_id))
    #         return cur.fetchall()
    #     finally:
    #         cur.close()
    #         conn.close()
            
    # income/repository.py

    @staticmethod
    def get_by_society(society_id):
        """
        Fetches combined income. 
        Fixed: Separates Flat Identity from the Billing Month/Year.
        """
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                -- 1. Get Other Income (Donations/Parking)
                SELECT 
                    income_date as date, 
                    source_name as source, 
                    description as period, 
                    amount, 
                    'Other' as type
                FROM other_income 
                WHERE society_id = %s
                
                UNION ALL
                
                -- 2. Get Paid Maintenance
                SELECT 
                    m.created_at::date as date, 
                    ('Flat ' || f.flat_number) as source, 
                    (m.month || ' ' || m.year) as period, 
                    m.amount, 
                    'Maintenance' as type
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN blocks b ON f.block_id = b.id
                WHERE b.society_id = %s AND m.status = 'paid'
                
                ORDER BY date DESC
            """, (society_id, society_id))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()