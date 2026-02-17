# from datetime import datetime
# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor
# from maintenance.repository import MaintenanceRepository
# from utils.mail import send_maintenance_reminder

# def auto_generate_maintenance(app):
#     """
#     1. Generates bills for every flat in the system.
#     2. Immediately finds the users and sends them an email.
#     """
#     with app.app_context():
#         print(f"--- STARTING AUTO-MAINTENANCE: {datetime.now()} ---")
        
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
        
#         # Simple string-based date parts
#         now = datetime.now()
#         month_name = now.strftime("%B")
#         year_num = now.year
#         # Simple YYYY-MM-DD string for Postgres
#         simple_due_date = f"{year_num}-{now.month:02d}-10" 

#         try:
#             # Step 1: Fetch all flats
#             cur.execute("SELECT id FROM flats")
#             flats = cur.fetchall()
#             flat_ids = [f['id'] for f in flats]

#             if not flat_ids:
#                 print("No flats found. Skipping.")
#                 return

#             # Step 2: Create the bills in DB
#             # We use 1500 as a standard default amount
#             MaintenanceRepository.bulk_create_maintenance(flat_ids, 1500, month_name, year_num, simple_due_date)
#             print(f"Generated bills for {len(flat_ids)} flats for {month_name}.")

#             # Step 3: Fetch UNPAID users for THIS month immediately
#             cur.execute("""
#                 SELECT u.email, u.full_name, m.amount, m.month, m.year 
#                 FROM maintenance m
#                 JOIN flats f ON m.flat_id = f.id
#                 JOIN users u ON f.owner_id = u.id
#                 WHERE m.month = %s AND m.year = %s 
#                 AND m.status = 'unpaid'
#                 AND u.email IS NOT NULL
#             """, (month_name, year_num))
            
#             recipients = cur.fetchall()
#             print(f"Sending emails to {len(recipients)} residents...")

#             # Step 4: Send the emails
#             for r in recipients:
#                 send_maintenance_reminder(
#                     r['email'], 
#                     r['full_name'], 
#                     r['amount'], 
#                     r['month'], 
#                     r['year']
#                 )

#             print("--- AUTO-MAINTENANCE COMPLETED SUCCESSFULLY ---")

#         except Exception as e:
#             print(f"CRITICAL ERROR IN SCHEDULER: {e}")
#         finally:
#             cur.close()
#             conn.close()

#     # utils/scheduler.py

#     def run_automated_maintenance(app):
#         with app.app_context():
#             conn = get_db_connection()
#             cur = conn.cursor(cursor_factory=RealDictCursor)
            
#             # ... month, year, due_date logic ...

#             try:
#                 # CHANGE: Fetch all flats globally that are occupied
#                 cur.execute("SELECT id FROM flats WHERE is_occupied = TRUE")
#                 flats = cur.fetchall()
#                 flat_ids = [f['id'] for f in flats]

#                 if flat_ids:
#                     # Generate bills (using standard amount 1500 or logic)
#                     MaintenanceRepository.bulk_create_maintenance(flat_ids, 1500, month_name, year_num, due_date)
                
#                 # ... existing mailing logic ...



from datetime import datetime
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from maintenance.repository import MaintenanceRepository
from utils.mail import send_maintenance_reminder

def auto_generate_maintenance(app):
    """
    Background Task: 
    1. Generates bills for OCCUPIED flats only.
    2. Immediately emails residents who have unpaid dues.
    """
    with app.app_context():
        print(f"--- [SCHEDULER START: {datetime.now()}] ---")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        now = datetime.now()
        month_name = now.strftime("%B")
        year_num = now.year
        # Default due date as 10th of the month
        simple_due_date = f"{year_num}-{now.month:02d}-10" 

        try:
            # STEP 1: Fetch IDs of all flats that are currently OCCUPIED
            cur.execute("SELECT id FROM flats WHERE is_occupied = TRUE")
            occupied_flats = cur.fetchall()
            flat_ids = [f['id'] for f in occupied_flats]

            if not flat_ids:
                print("LOG: No occupied flats found. Skipping generation.")
            else:
                # STEP 2: Create the bills in DB (Default amount 1500)
                # Repo method uses 'ON CONFLICT DO NOTHING' to prevent duplicates
                MaintenanceRepository.bulk_create_maintenance(flat_ids, 1500, month_name, year_num, simple_due_date)
                print(f"LOG: Generated bills for {len(flat_ids)} occupied units.")

            # STEP 3: Fetch UNPAID users for THIS specific month to send emails
            cur.execute("""
                SELECT u.email, u.full_name, m.amount, m.month, m.year 
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN users u ON f.owner_id = u.id
                WHERE m.month = %s AND m.year = %s 
                AND m.status = 'unpaid'
                AND u.email IS NOT NULL
            """, (month_name, year_num))
            
            recipients = cur.fetchall()
            print(f"LOG: Sending notification emails to {len(recipients)} residents...")

            # STEP 4: Trigger the emails
            for r in recipients:
                send_maintenance_reminder(
                    r['email'], 
                    r['full_name'], 
                    r['amount'], 
                    r['month'], 
                    r['year']
                )

            print("--- [SCHEDULER SUCCESSFUL] ---")

        except Exception as e:
            print(f"!!! SCHEDULER ERROR: {str(e)}")
            # No rollback needed here as repo methods handle their own commits
        finally:
            cur.close()
            conn.close()