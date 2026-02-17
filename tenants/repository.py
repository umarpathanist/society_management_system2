# from database.connection import get_db_connection


# class tenantRepository:
#     @staticmethod
#     def get_all():
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM tenants ORDER BY id DESC")
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows
