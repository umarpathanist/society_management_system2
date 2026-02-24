from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from income.repository import IncomeRepository
from societies.repository import SocietyRepository
from datetime import date

income_bp = Blueprint("income", __name__, url_prefix="/income")

# ---------------------------------------------------------
# 1. LIST INCOME (Combined Ledger View)
# ---------------------------------------------------------
@income_bp.route("/")
@login_required
def list_income():
    """
    Fetches the combined ledger (Maintenance + Other Income).
    FIXES: AssertionError - ensuring this function exists only once.
    """
    user = session.get("user")
    role = user.get("role").lower()
    
    # Super Admin can filter by society, others are forced to their own
    if role == "super_admin":
        selected_soc_id = request.args.get("society_id")
        societies = SocietyRepository.get_all()
    else:
        selected_soc_id = session.get("society_id")
        societies = []

    # Fetch records using the standardized combined ledger method
    records = IncomeRepository.get_combined_ledger(selected_soc_id) if selected_soc_id else []

    return render_template("income/list.html", 
                           records=records, 
                           societies=societies, 
                           selected_soc=int(selected_soc_id) if selected_soc_id else None,
                           role=role)

# ---------------------------------------------------------
# 2. ADD INCOME
# ---------------------------------------------------------
# @income_bp.route("/add", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "super_admin")
# def add_income():
#     """Handles adding new miscellaneous income entries."""
#     user = session.get("user")
#     role = user.get("role").lower()

#     if request.method == "POST":
#         target_society_id = request.form.get("society_id") if role == "super_admin" else session.get("society_id")

#         try:
#             IncomeRepository.add({
#                 "society_id": target_society_id,
#                 "source_name": request.form.get("source_name"),
#                 "amount": request.form.get("amount"),
#                 "income_date": request.form.get("income_date") or date.today(),
#                 "description": request.form.get("description")
#             })
#             flash("Income added successfully! ✅", "success")
#             return redirect(url_for("income.list_income"))
#         except Exception as e:
#             flash(f"Error: {str(e)}", "danger")

#     societies = SocietyRepository.get_all() if role == "super_admin" else []
#     return render_template("income/add.html", societies=societies, role=role)



@income_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "super_admin")
def add_income():
    user = session.get("user")
    role = user.get("role").lower()

    if request.method == "POST":
        # 1. Capture and Validate ID
        raw_soc_id = request.form.get("society_id")
        
        # Security: Prevent saving if ID is missing or string 'None'
        if not raw_soc_id or raw_soc_id == "None":
            flash("Error: Society context lost. Please try again from the Ledger page.", "danger")
            return redirect(url_for("income.list_income"))

        try:
            IncomeRepository.add({
                "society_id": int(raw_soc_id), # Force convert to integer
                "source_name": request.form.get("source_name"),
                "amount": float(request.form.get("amount") or 0),
                "income_date": request.form.get("income_date") or date.today(),
                "description": request.form.get("description")
            })
            flash("Income recorded successfully! ✅", "success")
            return redirect(url_for("income.list_income", society_id=raw_soc_id))
        except Exception as e:
            flash(f"Database Error: {str(e)}", "danger")

    # --- GET REQUEST LOGIC ---
    # 2. Get the ID from the URL (?society_id=9) or from Treasurer's session
    selected_id = request.args.get("society_id") or session.get("society_id")
    
    # 3. Fetch name for the UI header
    soc_name = "Unknown Building"
    if selected_id:
        soc_details = SocietyRepository.get_by_id(selected_id)
        if soc_details:
            soc_name = soc_details['name']

    return render_template("income/add.html", 
                           society_id=selected_id, 
                           society_name=soc_name)