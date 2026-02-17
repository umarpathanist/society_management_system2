
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
#                 return redirect(url_for("dashboard.index"))
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
#                 return redirect(url_for("dashboard.index"))
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
#             return redirect(url_for("dashboard.index"))
            
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
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from dateutil.relativedelta import relativedelta
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

@treasurers_bp.route("/get-next-unpaid/<int:flat_id>")
@login_required
def get_next_unpaid(flat_id):
    """AJAX endpoint to determine the starting period for collection."""
    res = MaintenanceRepository.get_next_unpaid_month(flat_id)
    
    if res:
        # If the result found was a 'paid' record, increment to the next month
        if res.get('type') == 'all_paid':
            m_num = MONTH_MAP.get(res['month'])
            y_num = int(res['year'])
            
            # Simple month-increment logic
            if m_num == 12: # December -> January next year
                next_month = "January"
                next_year = y_num + 1
            else:
                next_month = REV_MONTH_MAP[m_num + 1]
                next_year = y_num
                
            return jsonify({"month": next_month, "year": next_year})
        
        # If it was an 'unpaid' debt, return as is
        return jsonify({"month": res['month'], "year": res['year']})
    
    # Fallback for flats with ZERO history: Start from current month
    now = datetime.now()
    return jsonify({
        "month": now.strftime("%B"), 
        "year": now.year
    })



# ---------------------------------------------------------
# 4. MAINTENANCE COLLECTION (ADVANCE PAYMENT)
# ---------------------------------------------------------
@treasurers_bp.route("/collect-maintenance", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "admin", "super_admin")
def collect_maintenance():
    society_id = session.get("society_id")
    
    if request.method == "POST":
        flat_id = request.form.get("flat_id")
        amount = request.form.get("amount")
        s_month = request.form.get("start_month")
        s_year = request.form.get("start_year")
        e_month = request.form.get("end_month")
        e_year = request.form.get("end_year")

        if not all([flat_id, s_month, s_year, e_month, e_year]):
            flash("Missing period data. Please wait for history to load.", "danger")
            return redirect(url_for("treasurers.collect_maintenance"))

        try:
            start_dt = datetime(int(s_year), MONTH_MAP[s_month], 1)
            end_dt = datetime(int(e_year), MONTH_MAP[e_month], 1)

            curr = start_dt
            count = 0
            while curr <= end_dt:
                m_name = REV_MONTH_MAP[curr.month]
                y_num = curr.year
                
                # If bill doesn't exist, create it as paid
                bill = MaintenanceRepository.get_bill_status(flat_id, m_name, y_num)
                if not bill:
                    MaintenanceRepository.bulk_create_maintenance([flat_id], float(amount), m_name, y_num, curr.strftime('%Y-%m-10'))
                
                MaintenanceRepository.mark_as_paid_manually(flat_id, m_name, y_num)
                curr += relativedelta(months=1)
                count += 1

            flash(f"Advance payment for {count} months successful! ✅", "success")
            return redirect(url_for("dashboard.index"))
        except Exception as e:
            flash(f"Payment Failed: {str(e)}", "danger")
            return redirect(url_for("treasurers.collect_maintenance"))

    from blocks.repository import BlockRepository
    blocks = BlockRepository.get_by_society(society_id)
    return render_template("treasurers/collect_maintenance.html", blocks=blocks)

# ---------------------------------------------------------
# 5. GENERATE MAINTENANCE
# ---------------------------------------------------------
@treasurers_bp.route("/generate-maintenance", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "super_admin")
def generate_maintenance():
    society_id = session.get("society_id")
    if request.method == "POST":
        amount = request.form.get("amount")
        month = request.form.get("month")
        year = request.form.get("year")
        due_date = request.form.get("due_date")

        flats = FlatRepository.get_all_by_society(society_id)
        if flats:
            flat_ids = [f['id'] for f in flats]
            MaintenanceRepository.bulk_create_maintenance(flat_ids, amount, month, year, due_date)
            flash("Monthly bills generated! ✅", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("treasurers/generate_maintenance.html")

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
