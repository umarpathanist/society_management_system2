
# from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
# from datetime import datetime
# from utils.decorators import login_required, role_required
# from database.connection import get_db_connection
# from psycopg2.extras import RealDictCursor
# import calendar
# from dateutil.relativedelta import relativedelta

# # Repositories & Utilities
# from treasurers.service import TreasurerService
# from societies.repository import SocietyRepository
# from flats.repository import FlatRepository
# from blocks.repository import BlockRepository
# from maintenance.repository import MaintenanceRepository
# from utils.mail import send_maintenance_reminder

# treasurers_bp = Blueprint("treasurers", __name__, url_prefix="/treasurers")

# # ---------------------------------------------------------
# # 1. LIST TREASURERS (Fixes BuildError: treasurers.list)
# # ---------------------------------------------------------
# @treasurers_bp.route("/list")
# @login_required
# @role_required("super_admin")
# def list():
#     treasurers = TreasurerService.list_all()
#     return render_template("treasurers/list.html", treasurers=treasurers)

# # ---------------------------------------------------------
# # 2. ADD TREASURER
# # ---------------------------------------------------------
# @treasurers_bp.route("/add", methods=["GET", "POST"])
# @login_required
# @role_required("admin", "super_admin")
# def add():
#     user = session.get("user")
#     if request.method == "POST":
#         soc_id = request.form.get("society_id") if user['role'] == 'super_admin' else session.get("society_id")
#         try:
#             TreasurerService.add_treasurer({
#                 "full_name": request.form.get("full_name"),
#                 "email": request.form.get("email"),
#                 "password": request.form.get("password"),
#                 "society_id": soc_id
#             })
#             flash("Treasurer added successfully! ✅", "success")
#             return redirect(url_for("treasurers.list") if user['role'] == 'super_admin' else url_for("societies.list_societies"))
#         except ValueError as e:
#             flash(str(e), "warning")
#         except Exception as e:
#             flash(f"Error: {str(e)}", "danger")

#     societies = SocietyRepository.get_all() if user['role'] == 'super_admin' else []
#     return render_template("treasurers/add.html", role=user['role'], societies=societies)

# # ---------------------------------------------------------
# # 3. EDIT TREASURER
# # ---------------------------------------------------------
# @treasurers_bp.route("/edit/<int:id>", methods=["GET", "POST"])
# @login_required
# @role_required("super_admin")
# def edit(id):
#     treasurer = TreasurerService.get_treasurer(id)
#     if not treasurer:
#         flash("Treasurer not found", "danger")
#         return redirect(url_for("treasurers.list"))

#     if request.method == "POST":
#         try:
#             TreasurerService.update_treasurer(id, {
#                 "full_name": request.form.get("full_name"),
#                 "email": request.form.get("email"),
#                 "society_id": request.form.get("society_id"),
#                 "password": request.form.get("password")
#             })
#             flash("Treasurer updated! ✅", "success")
#             return redirect(url_for("treasurers.list"))
#         except Exception as e:
#             flash(f"Update Error: {str(e)}", "danger")

#     societies = SocietyRepository.get_all()
#     return render_template("treasurers/edit.html", treasurer=treasurer, societies=societies)

# # ---------------------------------------------------------
# # 4. DELETE TREASURER
# # ---------------------------------------------------------
# @treasurers_bp.route("/delete/<int:id>", methods=["POST"])
# @login_required
# @role_required("super_admin")
# def delete(id):
#     try:
#         TreasurerService.delete_treasurer(id)
#         flash("Treasurer removed. ✅", "success")
#     except Exception as e:
#         flash(f"Error: {str(e)}", "danger")
#     return redirect(url_for("treasurers.list"))

# # ---------------------------------------------------------
# # 5. GENERATE MAINTENANCE & SEND ALERTS
# # ---------------------------------------------------------
# @treasurers_bp.route("/generate-maintenance", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "super_admin")
# def generate_maintenance():
#     society_id = session.get("society_id")

#     if request.method == "POST":
#         action = request.form.get("action")
        
#         if action == "generate":
#             amount = request.form.get("amount")
#             flats = FlatRepository.get_occupied_by_society(society_id)
#             if not flats:
#                 flash("No occupied flats found.", "warning")
#                 return redirect(url_for("treasurers.generate_maintenance"))

#             flat_ids = [f['id'] for f in flats]
#             try:
#                 MaintenanceRepository.bulk_create_maintenance(flat_ids, amount, 
#                                                              request.form.get("month"), 
#                                                              request.form.get("year"), 
#                                                              request.form.get("due_date"))
#                 flash(f"Bills generated for {len(flat_ids)} units! ✅", "success")
#                 return redirect(url_for("dashboard.index_redirect"))
#             except Exception as e:
#                 flash(f"Error: {str(e)}", "danger")

#         elif action == "remind":
#             conn = get_db_connection()
#             cur = conn.cursor(cursor_factory=RealDictCursor)
#             try:
#                 cur.execute("""
#                     SELECT u.email, u.full_name, m.amount, m.month, m.year 
#                     FROM maintenance m
#                     JOIN flats f ON m.flat_id = f.id
#                     JOIN blocks b ON f.block_id = b.id
#                     JOIN users u ON f.owner_id = u.id
#                     WHERE b.society_id = %s AND m.status = 'unpaid' AND u.email IS NOT NULL
#                 """, (society_id,))
#                 unpaid_members = cur.fetchall()
#                 for m in unpaid_members:
#                     send_maintenance_reminder(m['email'], m['full_name'], m['amount'], m['month'], m['year'])
#                 flash(f"Manual reminders sent to {len(unpaid_members)} residents! 📩", "info")
#                 return redirect(url_for("dashboard.index_redirect"))
#             except Exception as e:
#                 flash(f"Mailing Error: {str(e)}", "danger")
#             finally:
#                 cur.close(); conn.close()

#     return render_template("treasurers/generate_maintenance.html")

# # ---------------------------------------------------------
# # 6. COLLECT MAINTENANCE (Manual recording)
# # ---------------------------------------------------------

# # @treasurers_bp.route("/collect-maintenance", methods=["GET", "POST"])
# # @login_required
# # @role_required("treasurer", "admin", "super_admin")
# # def collect_maintenance():
# #     society_id = session.get("society_id")
# #     blocks = BlockRepository.get_by_society(society_id)
    
# #     if request.method == "POST":
# #         flat_id = request.form.get("flat_id")
# #         month = request.form.get("start_month")
# #         year = request.form.get("start_year")
        
# #         try:
# #             from maintenance.repository import MaintenanceRepository
            
# #             # 1. VALIDATION: Check if bill exists and its current status
# #             bill = MaintenanceRepository.get_bill_status(flat_id, month, year)
            
# #             if not bill:
# #                 flash(f"Error: No maintenance bill has been generated for {month} {year} yet.", "warning")
# #                 return redirect(url_for("treasurers.collect_maintenance"))
            
# #             if bill['status'] == 'paid':
# #                 # --- THE FIX: SHOW ERROR IF ALREADY PAID ---
# #                 flash(f"Error: Maintenance for {month} {year} is already paid! ❌", "danger")
# #                 return redirect(url_for("treasurers.collect_maintenance"))

# #             # 2. PROCEED: If unpaid, record the payment
# #             MaintenanceRepository.mark_as_paid_manually(flat_id, month, year)
# #             flash(f"Payment for {month} {year} recorded successfully! ✅", "success")
            
# #         except Exception as e:
# #             flash(f"System Error: {str(e)}", "danger")

# #         return redirect(url_for("treasurers.collect_maintenance"))

# #     return render_template("treasurers/collect_maintenance.html", blocks=blocks)


# # treasurers/routes.py
# from dateutil.relativedelta import relativedelta

# @treasurers_bp.route("/collect-maintenance", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "admin", "super_admin")
# def collect_maintenance():
#     society_id = session.get("society_id")
    
#     if request.method == "POST":
#         flat_id = request.form.get("flat_id")
#         amount = request.form.get("amount")
        
#         s_month = request.form.get("start_month")
#         s_year = request.form.get("start_year")
#         e_month = request.form.get("end_month")
#         e_year = request.form.get("end_year")

#         # --- CRITICAL FIX: VALIDATION ---
#         if not all([flat_id, s_month, s_year, e_month, e_year]):
#             flash("Error: Missing payment period data. Please select a flat and wait for status to load.", "danger")
#             return redirect(url_for("treasurers.collect_maintenance"))

#         try:
#             # Convert strings to integers safely
#             start_dt = datetime(int(s_year), MONTH_MAP[s_month], 1)
#             end_dt = datetime(int(e_year), MONTH_MAP[e_month], 1)

#             if start_dt > end_dt:
#                 flash("Start date cannot be after end date.", "warning")
#                 return redirect(url_for("treasurers.collect_maintenance"))

#             curr = start_dt
#             while curr <= end_dt:
#                 m_name = REV_MONTH_MAP[curr.month]
#                 y_num = curr.year
                
#                 # Check if bill exists
#                 bill = MaintenanceRepository.get_bill_status(flat_id, m_name, y_num)
                
#                 if not bill:
#                     # Create paid bill for future months
#                     MaintenanceRepository.bulk_create_maintenance([flat_id], float(amount), m_name, y_num, curr.strftime('%Y-%m-10'))
                
#                 # Always mark as paid
#                 MaintenanceRepository.mark_as_paid_manually(flat_id, m_name, y_num)
#                 curr += relativedelta(months=1)

#             flash("Advance payment processed successfully! ✅", "success")
#             return redirect(url_for("dashboard.index_redirect"))
            
#         except Exception as e:
#             flash(f"Payment Failed: {str(e)}", "danger")
#             return redirect(url_for("treasurers.collect_maintenance"))

#     from blocks.repository import BlockRepository
#     blocks = BlockRepository.get_by_society(society_id)
#     return render_template("treasurers/collect_maintenance.html", blocks=blocks)


# # treasurers/routes.py

# @treasurers_bp.route("/get-next-unpaid/<int:flat_id>")
# @login_required
# def get_next_unpaid(flat_id):
#     """AJAX: Returns the earliest month that needs payment."""
#     from maintenance.repository import MaintenanceRepository
    
#     res = MaintenanceRepository.get_next_unpaid_month(flat_id)
    
#     if res:
#         # Convert database row to a clean dictionary
#         return jsonify(dict(res))
    
#     # Fallback: If no bills exist at all, start from current month
#     now = datetime.now()
#     return jsonify({
#         "month": now.strftime("%B"), 
#         "year": now.year
#     })
# # ---------------------------------------------------------
# # 7. AJAX HELPER: GET OCCUPIED FLATS
# # ---------------------------------------------------------
# @treasurers_bp.route("/get-occupied-flats/<int:block_id>")
# @login_required
# def get_occupied_flats(block_id):
#     flats = FlatRepository.get_occupied_with_maintenance(block_id)
#     return {"flats": flats}






import calendar
from datetime import datetime
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session, jsonify
from dateutil.relativedelta import relativedelta
from extensions import get_razorpay_client
from utils.decorators import login_required, role_required

# Repositories
from treasurers.service import TreasurerService
from societies.repository import SocietyRepository
from flats.repository import FlatRepository
from maintenance.repository import MaintenanceRepository

treasurers_bp = Blueprint("treasurers", __name__, url_prefix="/treasurers")

# --- MONTH HELPER MAPS (FIXES: NameError 'MONTH_MAP') ---
MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}
REV_MONTH_MAP = {v: k for k, v in MONTH_MAP.items()}

# ---------------------------------------------------------
# 1. LIST TREASURERS
# ---------------------------------------------------------
@treasurers_bp.route("/list")
@login_required
@role_required("super_admin")
def list():
    treasurers = TreasurerService.list_all()
    return render_template("treasurers/list.html", treasurers=treasurers)

# ---------------------------------------------------------
# 2. ADD TREASURER
# ---------------------------------------------------------
@treasurers_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def add():
    user = session.get("user")
    role = user.get("role")
    
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        soc_id = request.form.get("society_id") if role == "super_admin" else session.get("society_id")

        try:
            TreasurerService.add_treasurer({
                "full_name": full_name, "email": email,
                "password": password, "society_id": soc_id
            })
            flash("Treasurer added successfully! ✅", "success")
            return redirect(url_for("treasurers.list") if role == "super_admin" else url_for("societies.list_societies"))
        except ValueError as e:
            flash(str(e), "warning")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    societies = SocietyRepository.get_all() if role == 'super_admin' else []
    return render_template("treasurers/add.html", role=role, societies=societies)

# ---------------------------------------------------------
# 3. AJAX HELPERS
# ---------------------------------------------------------
@treasurers_bp.route("/get-occupied-flats/<int:block_id>")
@login_required
def get_occupied_flats(block_id):
    flats = FlatRepository.get_by_block(block_id)
    occupied = [f for f in flats if f.get('owner_name') or f.get('tenant_name')]
    return jsonify({"flats": occupied})

# treasurers/routes.py
# treasurers/routes.py

@treasurers_bp.route("/get-next-unpaid/<int:flat_id>")
@login_required
def get_next_unpaid(flat_id):
    """
    Standardized API endpoint. 
    FIXED: Now calling the correct method name 'get_next_unpaid_bill'
    """
    # Use 'get_next_unpaid_bill' NOT 'get_next_unpaid_month'
    bill = MaintenanceRepository.get_next_unpaid_bill(flat_id)
    
    if bill:
        return jsonify({
            "id": bill['id'],
            "month": bill['month'],
            "year": bill['year'],
            "amount": float(bill['amount'])
        })
    
    # If no bill is found, return 404
    return jsonify({"error": "No unpaid bills"}), 404
# ---------------------------------------------------------
# 4. MAINTENANCE COLLECTION (ADVANCE PAYMENT)
# ---------------------------------------------------------
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from treasurers.service import TreasurerService
from societies.repository import SocietyRepository
from blocks.repository import BlockRepository
from maintenance.repository import MaintenanceRepository

# Month mappings for date calculations
MONTH_MAP = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
REV_MONTH_MAP = {v: k for k, v in MONTH_MAP.items()}

@treasurers_bp.route("/collect-maintenance", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "admin", "super_admin")
def collect_maintenance():
    """
    Handles maintenance collection.
    FIXED: Fetches societies for Super Admin dropdown on GET request.
    """
    user = session.get("user")
    role = user.get("role", "").lower() # Get role safely
    
    # 1. Determine target society (Super Admin uses URL filter, others use session)
    selected_soc_id = request.args.get("society_id") if role == "super_admin" else session.get("society_id")

    # ---------------------------------------------------------
    # POST LOGIC: Same as before...
    # ---------------------------------------------------------
    if request.method == "POST":
        flat_id = request.form.get("flat_id")
        amount = request.form.get("amount")
        s_month = request.form.get("start_month")
        s_year = request.form.get("start_year")
        e_month = request.form.get("end_month")
        e_year = request.form.get("end_year")

        if not all([flat_id, s_month, s_year, e_month, e_year]):
            flash("Data missing. Please select a flat and let history load.", "warning")
            return redirect(url_for("treasurers.collect_maintenance", society_id=selected_soc_id))

        try:
            start_dt = datetime(int(s_year), MONTH_MAP[s_month], 1)
            end_dt = datetime(int(e_year), MONTH_MAP[e_month], 1)
            curr = start_dt
            count = 0
            while curr <= end_dt:
                m_name = REV_MONTH_MAP[curr.month]
                y_num = curr.year
                bill = MaintenanceRepository.get_by_flat_id_month_year(flat_id, m_name, y_num)
                if not bill:
                    MaintenanceRepository.bulk_create_maintenance([flat_id], float(amount), m_name, y_num, curr.strftime('%Y-%m-10'))
                MaintenanceRepository.mark_as_paid_manually(flat_id, m_name, y_num)
                curr += relativedelta(months=1)
                count += 1
            flash(f"Advance payment for {count} months successful! ✅", "success")
            return redirect(url_for("dashboard.index_redirect"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for("treasurers.collect_maintenance", society_id=selected_soc_id))

    # ---------------------------------------------------------
    # GET LOGIC: Fetch data to fill dropdowns
    # ---------------------------------------------------------
    
    # FETCH SOCIETIES: Only for Super Admin
    societies_data = []
    if role == "super_admin":
        from societies.repository import SocietyRepository
        societies_data = SocietyRepository.get_all()
        # DEBUG: Look at your VS Code terminal to see if this prints
        print(f"DEBUG: Found {len(societies_data)} societies for the dropdown.")

    # FETCH BLOCKS: Filtered by the selected society
    blocks_data = []
    if selected_soc_id:
        from blocks.repository import BlockRepository
        blocks_data = BlockRepository.get_by_society(selected_soc_id)
        print(f"DEBUG: Found {len(blocks_data)} blocks for society ID {selected_soc_id}.")

    return render_template(
        "treasurers/collect_maintenance.html", 
        societies=societies_data, # Variable for the dropdown
        blocks=blocks_data,       # Variable for the blocks list
        selected_soc=int(selected_soc_id) if selected_soc_id else None,
        role=role
    )



# ---------------------------------------------------------
# 5. GENERATE MAINTENANCE
# ---------------------------------------------------------
# @treasurers_bp.route("/generate-maintenance", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "super_admin")
# def generate_maintenance():
#     """
#     Handles manual billing and reminders.
#     REDIRECTIONS: Fixed to stay on the same page.
#     FILTER: Bills are generated ONLY for currently occupied units.
#     """
#     user = session.get("user")
#     role = user.get("role").lower()
#     session_soc_id = session.get("society_id")
    
#     if request.method == "POST":
#         action = request.form.get("action")
        
#         # Determine target society based on role and form input
#         target_society_id = request.form.get("society_id") if role == "super_admin" else session_soc_id

#         if not target_society_id:
#             flash("Please select a target society first.", "warning")
#             return redirect(url_for("treasurers.generate_maintenance"))

#         from database.connection import get_db_connection
#         from psycopg2.extras import RealDictCursor
#         from utils.mail import send_maintenance_reminder
        
#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         try:
#             # ---------------------------------------------------------
#             # ACTION 1: MANUAL BILL GENERATION (OCCUPIED ONLY)
#             # ---------------------------------------------------------
#             if action == "generate":
#                 amount = request.form.get("amount")
#                 month = request.form.get("month")
#                 year = request.form.get("year")
#                 due_date = request.form.get("due_date")

#                 if not all([amount, month, year, due_date]):
#                     flash("Missing billing details. Please fill all fields.", "danger")
#                 else:
#                     # FETCH ONLY OCCUPIED FLATS FROM DB
#                     occupied_flats = FlatRepository.get_occupied_by_society(target_society_id)
                    
#                     if not occupied_flats:
#                         flash("No occupied flats found in the selected society. Vacant units were not billed.", "warning")
#                     else:
#                         flat_ids = [f['id'] for f in occupied_flats]
                        
#                         # Bulk create records in Maintenance table
#                         MaintenanceRepository.bulk_create_maintenance(
#                             flat_ids, float(amount), month, int(year), due_date
#                         )
#                         flash(f"Success! Bills generated for {len(flat_ids)} occupied units. Vacant units skipped. ✅", "success")

#             # ---------------------------------------------------------
#             # ACTION 2: INSTANT EMAIL REMINDERS
#             # ---------------------------------------------------------
#             elif action == "remind":
#                 cur.execute("""
#                     SELECT u.email, u.full_name, m.amount, m.month, m.year 
#                     FROM maintenance m
#                     JOIN flats f ON m.flat_id = f.id
#                     JOIN blocks b ON f.block_id = b.id
#                     JOIN users u ON f.owner_id = u.id
#                     WHERE b.society_id = %s 
#                       AND m.status = 'unpaid'
#                       AND u.email IS NOT NULL
#                 """, (target_society_id,))
                
#                 unpaid_members = cur.fetchall()
                
#                 if unpaid_members:
#                     for member in unpaid_members:
#                         send_maintenance_reminder(
#                             member['email'], member['full_name'], 
#                             member['amount'], member['month'], member['year']
#                         )
#                     flash(f"Email Campaign: {len(unpaid_members)} reminders dispatched! 📩", "info")
#                 else:
#                     flash("Everyone is up to date! No reminders needed. ✨", "success")

#             # STAY ON THE SAME PAGE AFTER POST
#             return redirect(url_for("treasurers.generate_maintenance"))

#         except Exception as e:
#             print(f"CRITICAL ERROR: {e}")
#             flash(f"System Error: {str(e)}", "danger")
#             if conn: conn.rollback()
#             return redirect(url_for("treasurers.generate_maintenance"))
#         finally:
#             cur.close()
#             conn.close()
           
            

#     # --- GET REQUEST: LOAD SOCIETIES FOR SUPER ADMIN ---
#     societies_list = []
#     if role == "super_admin":
#         from societies.repository import SocietyRepository
#         societies_list = SocietyRepository.get_all()

#     return render_template(
#         "treasurers/generate_maintenance.html", 
#         societies=societies_list 
#     )

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from societies.repository import SocietyRepository
from flats.repository import FlatRepository
from maintenance.repository import MaintenanceRepository
from notifications.repository import NotificationRepository
from database.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from utils.mail import send_maintenance_reminder
from datetime import datetime

# @treasurers_bp.route("/generate-maintenance", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "super_admin")
# def generate_maintenance():
#     """
#     Handles manual billing and reminders.
#     Logic:
#     1. Bills generated ONLY for currently occupied units.
#     2. Triggers in-app notifications for billed owners.
#     3. Allows sending bulk email reminders for unpaid dues.
#     """
#     user = session.get("user")
#     role = user.get("role").lower()
#     session_soc_id = session.get("society_id")
    
#     if request.method == "POST":
#         action = request.form.get("action")
#         target_society_id = request.form.get("society_id") if role == "super_admin" else session_soc_id

#         if not target_society_id:
#             flash("Please select a target society first.", "warning")
#             return redirect(url_for("treasurers.generate_maintenance"))

#         from database.connection import get_db_connection
#         from psycopg2.extras import RealDictCursor
#         from utils.mail import send_maintenance_reminder
#         from notifications.repository import NotificationRepository

#         conn = get_db_connection()
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         try:
#             # ---------------------------------------------------------
#             # ACTION 1: MANUAL BILL GENERATION (OCCUPIED ONLY + NOTIFICATIONS)
#             # ---------------------------------------------------------
#             if action == "generate":
#                 amount = request.form.get("amount")
#                 month = request.form.get("month")
#                 year = request.form.get("year")
#                 due_date = request.form.get("due_date")

#                 if not all([amount, month, year, due_date]):
#                     flash("Missing billing details. Please fill all fields.", "danger")
#                 else:
#                     # A. Fetch ONLY occupied flats for the specific society
#                     occupied_flats = FlatRepository.get_occupied_by_society(target_society_id)
                    
#                     if not occupied_flats:
#                         flash("No occupied flats found. Vacant units were not billed.", "warning")
#                     else:
#                         flat_ids = [f['id'] for f in occupied_flats]
                        
#                         # B. Bulk generate records in Maintenance table
#                         MaintenanceRepository.bulk_create_maintenance(
#                             flat_ids, float(amount), month, int(year), due_date
#                         )

#                         # C. Fetch unique owners to trigger in-app notifications
#                         cur.execute("""
#                             SELECT DISTINCT owner_id, full_name 
#                             FROM flats f
#                             JOIN users u ON f.owner_id = u.id
#                             WHERE f.id = ANY(%s) AND f.owner_id IS NOT NULL
#                         """, (flat_ids,))
                        
#                         billed_owners = cur.fetchall()
                        
#                         # D. Create the Notifications
#                         for owner in billed_owners:
#                             NotificationRepository.create(
#                                 user_id=owner['owner_id'],
#                                 title="New Maintenance Bill 🧾",
#                                 message=f"A new bill of Rs.{amount} for {month} {year} has been generated. Due: {due_date}",
#                                 notif_type="due"
#                             )

#                         flash(f"Success! Generated {len(flat_ids)} bills and notified {len(billed_owners)} owners! ✅", "success")

#             # ---------------------------------------------------------
#             # ACTION 2: INSTANT EMAIL REMINDERS
#             # ---------------------------------------------------------
#             elif action == "remind":
#                 cur.execute("""
#                     SELECT u.email, u.full_name, m.amount, m.month, m.year 
#                     FROM maintenance m
#                     JOIN flats f ON m.flat_id = f.id
#                     JOIN blocks b ON f.block_id = b.id
#                     JOIN users u ON f.owner_id = u.id
#                     WHERE b.society_id = %s 
#                       AND m.status = 'unpaid'
#                       AND u.email IS NOT NULL
#                 """, (target_society_id,))
                
#                 unpaid_members = cur.fetchall()
                
#                 if unpaid_members:
#                     for member in unpaid_members:
#                         send_maintenance_reminder(
#                             member['email'], member['full_name'], 
#                             member['amount'], member['month'], member['year']
#                         )
#                     flash(f"Success: {len(unpaid_members)} email reminders dispatched! 📩", "info")
#                 else:
#                     flash("Everyone has paid! No reminders needed. ✨", "success")

#             return redirect(url_for("dashboard.index_redirect"))

#         except Exception as e:
#             print(f"SYSTEM ERROR: {e}")
#             flash(f"Process failed: {str(e)}", "danger")
#             if conn: conn.rollback()
#             return redirect(url_for("treasurers.generate_maintenance"))
#         finally:
#             cur.close()
#             conn.close()

#     # --- GET REQUEST: LOAD SOCIETIES LIST FOR SUPER ADMIN ---
#     societies_list = []
#     if role == "super_admin":
#         societies_list = SocietyRepository.get_all()

#     return render_template(
#         "treasurers/generate_maintenance.html", 
#         societies=societies_list,
#         role=role
#     )

@treasurers_bp.route("/generate-maintenance", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "super_admin")
def generate_maintenance():
    user = session.get("user")
    role = user.get("role").lower()
    session_soc_id = session.get("society_id")
    
    if request.method == "POST":
        action = request.form.get("action")
        target_society_id = request.form.get("society_id") if role == "super_admin" else session_soc_id

        if not target_society_id:
            flash("Please select a target society first.", "warning")
            return redirect(url_for("treasurers.generate_maintenance"))

        from database.connection import get_db_connection
        from psycopg2.extras import RealDictCursor
        from utils.mail import send_maintenance_reminder
        
        # Safe import for notifications
        try:
            from notifications.repository import NotificationRepository
        except ImportError:
            NotificationRepository = None 

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # ---------------------------------------------------------
            # ACTION 1: MANUAL BILL GENERATION (Email both Owner & Tenant)
            # ---------------------------------------------------------
            if action == "generate":
                amount = request.form.get("amount")
                month = request.form.get("month")
                year = request.form.get("year")
                due_date = request.form.get("due_date")

                if not all([amount, month, year, due_date]):
                    flash("Missing billing details. Please fill all fields.", "danger")
                else:
                    # 1. Fetch all flats that should be billed
                    occupied_flats = FlatRepository.get_occupied_by_society(target_society_id)
                    
                    if not occupied_flats:
                        flash("No occupied flats found in your society to generate bills.", "warning")
                    else:
                        flat_ids = [f['id'] for f in occupied_flats]
                        
                        # A. Generate database records (Bulk Insert)
                        MaintenanceRepository.bulk_create_maintenance(
                            flat_ids, float(amount), month, int(year), due_date
                        )

                        # B. Fetch Emails for residents (Prefers Tenant email, falls back to Owner)
                        cur.execute("""
                            SELECT DISTINCT 
                                COALESCE(ut.email, uo.email) as email,
                                COALESCE(ut.full_name, uo.full_name) as full_name,
                                COALESCE(f.tenant_id, f.owner_id) as user_id
                            FROM flats f
                            LEFT JOIN users uo ON f.owner_id = uo.id
                            LEFT JOIN users ut ON f.tenant_id = ut.id
                            WHERE f.id = ANY(%s) 
                              AND (f.tenant_id IS NOT NULL OR f.owner_id IS NOT NULL)
                        """, (flat_ids,))
                        
                        recipients = cur.fetchall()
                        
                        # C. Send Emails and In-app Notifications
                        count = 0
                        for r in recipients:
                            if r['email']:
                                # Trigger Email
                                send_maintenance_reminder(
                                    r['email'], r['full_name'], 
                                    amount, month, year
                                )
                                # Trigger In-app Notification (If table exists)
                                if NotificationRepository:
                                    NotificationRepository.create(
                                        user_id=r['user_id'],
                                        title="New Bill Generated 🧾",
                                        message=f"Maintenance of ₹{amount} for {month} {year} is generated. Due: {due_date}",
                                        notif_type="due"
                                    )
                                count += 1

                        flash(f"Success! Generated bills and notified {count} residents via email. ✅", "success")

            # ---------------------------------------------------------
            # ACTION 2: EMAIL REMINDERS (FOR PENDING DUES ONLY)
            # ---------------------------------------------------------
            elif action == "remind":
                cur.execute("""
                    SELECT 
                        COALESCE(ut.email, uo.email) as email,
                        COALESCE(ut.full_name, uo.full_name) as full_name,
                        m.amount, m.month, m.year 
                    FROM maintenance m
                    JOIN flats f ON m.flat_id = f.id
                    JOIN blocks b ON f.block_id = b.id
                    LEFT JOIN users uo ON f.owner_id = uo.id
                    LEFT JOIN users ut ON f.tenant_id = ut.id
                    WHERE b.society_id = %s 
                      AND m.status = 'unpaid'
                      AND (ut.email IS NOT NULL OR uo.email IS NOT NULL)
                """, (target_society_id,))
                
                pending_users = cur.fetchall()
                
                for p in pending_users:
                    send_maintenance_reminder(
                        p['email'], p['full_name'], 
                        p['amount'], p['month'], p['year']
                    )
                
                flash(f"Sent {len(pending_users)} reminders to members with pending dues! 📩", "info")

            return redirect(url_for("dashboard.index_redirect"))

        except Exception as e:
            flash(f"Process failed: {str(e)}", "danger")
            if conn: conn.rollback()
        finally:
            cur.close()
            conn.close()

    societies_list = SocietyRepository.get_all() if role == "super_admin" else []
    return render_template("treasurers/generate_maintenance.html", societies=societies_list, role=role)

# ---------------------------------------------------------
# 6. DELETE TREASURER
# ---------------------------------------------------------
@treasurers_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
@role_required("super_admin")
def delete(id):
    TreasurerService.delete_treasurer(id)
    flash("Treasurer removed. ✅", "success")
    return redirect(url_for("treasurers.list"))


# ---------------------------------------------------------
# 3. EDIT TREASURER (FIXES BuildError: 'treasurers.edit')
# ---------------------------------------------------------
@treasurers_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def edit(id): # <--- Function name MUST be 'edit'
    treasurer = TreasurerService.get_treasurer(id)
    if not treasurer:
        flash("Treasurer not found", "danger")
        return redirect(url_for("treasurers.list"))

    if request.method == "POST":
        try:
            TreasurerService.update_treasurer(id, {
                "full_name": request.form.get("full_name"),
                "email": request.form.get("email"),
                "society_id": request.form.get("society_id"),
                "password": request.form.get("password")
            })
            flash("Treasurer profile updated! ✅", "success")
            return redirect(url_for("treasurers.list"))
        except Exception as e:
            flash(f"Update Error: {str(e)}", "danger")

    societies = SocietyRepository.get_all()
    return render_template("treasurers/edit.html", treasurer=treasurer, societies=societies)

# treasurers/routes.py

@treasurers_bp.route("/collect-payment", methods=["POST"])
@login_required
def collect_payment():
    data = request.get_json()
    flat_id = data.get("flat_id")
    mode = data.get("mode") 
    total = float(data.get("total_amount", 0))
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if mode == "cash":
        try:
            # We assume a monthly rate for the advance calculation
            # If paying for 1 month, rate = total. If 2 months, rate = total/2.
            # For simplicity, we use the value from the monthly_rate input
            rate = float(data.get("monthly_rate") or 1500)

            MaintenanceRepository.process_advance_payment(
                flat_id, start_date, end_date, rate, 'Cash'
            )
            
            flash(f"Payment of ₹{total:,.2f} recorded for Flat {data.get('flat_num')}! ✅", "success")
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    elif mode == "online":
        try:
            client = get_razorpay_client()
            order = client.order.create(data={
                "amount": int(total * 100), 
                "currency": "INR",
                "receipt": f"adv_{flat_id}_{int(datetime.now().timestamp())}"
            })
            # Add logic here to save order ID to DB if needed
            return jsonify({
                "status": "order_created",
                "id": order['id'],
                "amount": order['amount'],
                "key": current_app.config['RAZORPAY_KEY_ID'],
                "full_name": session['user']['full_name'],
                "email": session['user']['email']
            })
        except Exception as e:
            return jsonify({"status": "error", "message": f"Gateway Error: {str(e)}"}), 500
    

@treasurers_bp.route("/collect-payment", methods=["POST"])
@login_required
@role_required("treasurer", "super_admin")
def collect_payment_action():
    data = request.get_json()
    flat_id = data.get("flat_id")
    mode = data.get("mode") # 'cash' or 'online'
    total_amount = float(data.get("total_amount", 0))
    
    # Range details
    start_date_str = data.get("start_date") # YYYY-MM-01
    end_date_str = data.get("end_date")     # YYYY-MM-01

    if mode == "cash":
        try:
            # 1. Update/Insert records in DB via Repository
            MaintenanceRepository.process_advance_payment(
                flat_id, start_date_str, end_date_str, total_amount, 'Cash'
            )
            # 2. SET FLASH MESSAGE (It will appear after JS reloads the page)
            flash(f"Cash payment of ₹{total_amount:,.2f} recorded successfully for Flat {data.get('flat_num')}! ✅", "success")
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    elif mode == "online":
        try:
            # Create Razorpay Order
            client = get_razorpay_client()
            order = client.order.create(data={
                "amount": int(total_amount * 100), # Paise
                "currency": "INR",
                "receipt": f"adv_{flat_id}_{int(datetime.now().timestamp())}"
            })
            
            # Save Order ID for verification later
            MaintenanceRepository.save_order_id_for_range(flat_id, start_date_str, end_date_str, order['id'])
            
            return jsonify({
                "status": "order_created",
                "id": order['id'],
                "amount": order['amount'],
                "key": current_app.config['RAZORPAY_KEY_ID'],
                "full_name": session['user']['full_name'],
                "email": session['user']['email']
            })
        except Exception as e:
            return jsonify({"status": "error", "message": f"Gateway Error: {str(e)}"}), 500
