# from datetime import datetime
# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor
# from maintenance.repository import MaintenanceRepository
# from utils.mail import send_maintenance_reminder

# from datetime import datetime
# from flask import current_app
# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor
# from maintenance.repository import MaintenanceRepository
# from utils.mail import send_maintenance_reminder

# def auto_generate_maintenance(app):
#     """
#     Background Task: 
#     1. Generates bills for OCCUPIED flats only.
#     2. Sends email notifications only to those with 'unpaid' status for the current month.
#     """
#     with app.app_context():
#         print(f"--- [SCHEDULER START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ---")
        
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)
        
#         # Determine Current Billing Cycle
#         now = datetime.now()
#         month_name = now.strftime("%B") # e.g., 'February'
#         year_num = now.year
        
#         # Set due date as 10th of the current month
#         simple_due_date = f"{year_num}-{now.month:02d}-10" 
#         default_amount = 1500.00

#         try:
#             # STEP 1: Fetch IDs of all flats that are currently OCCUPIED
#             cur.execute("SELECT id FROM flats WHERE is_occupied = TRUE")
#             occupied_flats = cur.fetchall()
            
#             if not occupied_flats:
#                 print("LOG: No occupied flats found. Skipping generation loop.")
#             else:
#                 flat_ids = [f['id'] for f in occupied_flats]
                
#                 # STEP 2: Create bills in DB
#                 # Note: MaintenanceRepository.bulk_create_maintenance handles 'ON CONFLICT DO NOTHING'
#                 MaintenanceRepository.bulk_create_maintenance(
#                     flat_ids, 
#                     default_amount, 
#                     month_name, 
#                     year_num, 
#                     simple_due_date
#                 )
#                 print(f"LOG: Processed billing for {len(flat_ids)} occupied units.")

#             # STEP 3: Fetch residents with UNPAID bills for THIS month
#             # We join maintenance with users to get email details
#             cur.execute("""
#                 SELECT 
#                     u.email, 
#                     u.full_name, 
#                     m.amount, 
#                     m.month, 
#                     m.year 
#                 FROM maintenance m
#                 JOIN flats f ON m.flat_id = f.id
#                 JOIN users u ON f.owner_id = u.id
#                 WHERE m.month = %s 
#                   AND m.year = %s 
#                   AND m.status = 'unpaid'
#                   AND u.email IS NOT NULL
#             """, (month_name, year_num))
            
#             recipients = cur.fetchall()
            
#             # STEP 4: Send the notification emails
#             if not recipients:
#                 print(f"LOG: No unpaid bills found for {month_name}. No emails to send.")
#             else:
#                 print(f"LOG: Sending maintenance notifications to {len(recipients)} residents...")
#                 for r in recipients:
#                     send_maintenance_reminder(
#                         r['email'], 
#                         r['full_name'], 
#                         r['amount'], 
#                         r['month'], 
#                         r['year']
#                     )
#                 print("LOG: All email notifications sent.")

#             print("--- [SCHEDULER SUCCESSFUL] ---")

#         except Exception as e:
#             print(f"!!! SCHEDULER CRITICAL ERROR: {str(e)}")
#             if conn:
#                 conn.rollback()
#         finally:
#             if cur: cur.close()
#             if conn: conn.close()

from datetime import datetime
from flask import current_app
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from maintenance.repository import MaintenanceRepository
from utils.mail import send_maintenance_reminder


def auto_generate_maintenance(app):
    """
    Background Task:
    1. Generates bills for OCCUPIED flats only.
    2. Sends email notifications only to those with 'unpaid' status for the current month.
    """
    with app.app_context():
        print(f"--- [SCHEDULER START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ---")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Determine Current Billing Cycle
        now = datetime.now()
        month_name = now.strftime("%B")
        year_num = now.year

        # Due date = 10th of current month
        simple_due_date = f"{year_num}-{now.month:02d}-10"
        default_amount = 1500.00

        try:
            # STEP 1: Fetch OCCUPIED flats
            cur.execute("SELECT id FROM flats WHERE is_occupied = TRUE")
            occupied_flats = cur.fetchall()

            if not occupied_flats:
                print("LOG: No occupied flats found. Skipping generation loop.")
                flat_ids = []
            else:
                flat_ids = [f['id'] for f in occupied_flats]

                # STEP 2: Create maintenance bills
                MaintenanceRepository.bulk_create_maintenance(
                    flat_ids,
                    default_amount,
                    month_name,
                    year_num,
                    simple_due_date
                )

                print(f"LOG: Processed billing for {len(flat_ids)} occupied units.")

                # ✅ STEP 2.1: Create IN-APP notifications for all billed owners
                cur.execute("""
                    SELECT DISTINCT owner_id
                    FROM flats
                    WHERE is_occupied = TRUE
                      AND owner_id IS NOT NULL
                """)
                owners_to_notify = cur.fetchall()

                from notifications.repository import NotificationRepository

                for owner in owners_to_notify:
                    NotificationRepository.create(
                        user_id=owner['owner_id'],
                        title="Monthly Maintenance Ready 🔔",
                        message=f"Your maintenance dues for {month_name} {year_num} are now available.",
                        notif_type="due"
                    )

            # STEP 3: Fetch residents with UNPAID bills for current month
            cur.execute("""
                SELECT 
                    u.email,
                    u.full_name,
                    m.amount,
                    m.month,
                    m.year
                FROM maintenance m
                JOIN flats f ON m.flat_id = f.id
                JOIN users u ON f.owner_id = u.id
                WHERE m.month = %s
                  AND m.year = %s
                  AND m.status = 'unpaid'
                  AND u.email IS NOT NULL
            """, (month_name, year_num))

            recipients = cur.fetchall()

            # STEP 4: Send Email Notifications
            if not recipients:
                print(f"LOG: No unpaid bills found for {month_name}. No emails to send.")
            else:
                print(f"LOG: Sending maintenance notifications to {len(recipients)} residents...")

                for r in recipients:
                    send_maintenance_reminder(
                        r['email'],
                        r['full_name'],
                        r['amount'],
                        r['month'],
                        r['year']
                    )

                print("LOG: All email notifications sent.")

            print("--- [SCHEDULER SUCCESSFUL] ---")

        except Exception as e:
            print(f"!!! SCHEDULER CRITICAL ERROR: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


# Inside utils/scheduler.py
from tickets.repository import TicketRepository
from utils.mail import send_sla_escalation_email

def check_ticket_sla(app):
    """
    Scans for tickets older than 48 hours and notifies Admins.
    Called automatically by the background clock.
    """
    with app.app_context():
        print("LOG: Starting SLA Escalation Check...")
        try:
            overdue_tickets = TicketRepository.get_overdue_tickets()
            
            for t in overdue_tickets:
                send_sla_escalation_email(
                    admin_email=t['admin_email'],
                    admin_name=t['admin_name'],
                    ticket_id=t['ticket_id'],
                    ticket_title=t['title']
                )
                print(f"LOG: SLA Alert sent for Ticket #{t['ticket_id']} to {t['admin_email']}")
                
            print(f"LOG: SLA Check complete. {len(overdue_tickets)} escalations processed.")
        except Exception as e:
            print(f"SLA SCHEDULER ERROR: {e}")  

from datetime import datetime
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from flask_mail import Message
from extensions import mail
from utils.report_gen import generate_csv_report # Import correctly

def email_scheduled_reports(app):
    """
    Background Task: Sends weekly reports to all Society Admins.
    """
    with app.app_context():
        print(f"--- [REPORT SCHEDULER START: {datetime.now()}] ---")
        
        conn = get_db_connection()
        # FIXED: Cursor must be defined correctly on one line
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # 1. Find all active Society Admins
            cur.execute("""
                SELECT email, full_name, society_id 
                FROM users 
                WHERE role = 'admin' AND society_id IS NOT NULL
            """)
            admins = cur.fetchall()

            for adm in admins:
                # 2. Generate CSV for this admin's society
                csv_data = generate_csv_report(adm['society_id'])
                
                # 3. Create and send Email
                msg = Message(
                    subject=f"📊 Weekly Report - {datetime.now().strftime('%d %b %Y')}",
                    recipients=[adm['email']],
                    body=f"Hello {adm['full_name']},\n\nPlease find attached your weekly report."
                )
                msg.attach("weekly_report.csv", "text/csv", csv_data)
                mail.send(msg)
                print(f"LOG: Email sent to {adm['email']}")

        except Exception as e:
            print(f"!!! SCHEDULER ERROR: {e}")
        finally:
            cur.close()
            conn.close()