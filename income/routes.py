# from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# from utils.decorators import login_required, role_required
# from income.repository import IncomeRepository
# from societies.repository import SocietyRepository 
# from datetime import date

# income_bp = Blueprint("income", __name__, url_prefix="/income")

# # income/routes.py

# # income/routes.py
# @income_bp.route("/")
# @login_required
# def list_income():
#     user = session.get("user")
#     role = user.get("role").lower()
    
#     # 1. Logic for Super Admin (Filtering enabled)
#     if role == "super_admin":
#         selected_soc_id = request.args.get("society_id")
#         from societies.repository import SocietyRepository
#         societies = SocietyRepository.get_all()
#     # 2. Logic for Admin/Treasurer (Forced to their own society)
#     else:
#         selected_soc_id = session.get("society_id")
#         societies = [] # No need to load societies for dropdown

#     # Fetch records based on the ID determined above
#     records = IncomeRepository.get_by_society(selected_soc_id) if selected_soc_id else []

#     return render_template("income/list.html", 
#                            records=records, 
#                            societies=societies, 
#                            selected_soc=int(selected_soc_id) if selected_soc_id else None)


# @income_bp.route("/add", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "super_admin")
# def add_income():
#     if request.method == "POST":
#         try:
#             IncomeRepository.add({
#                 "society_id": request.form.get("society_id"), # Get from dropdown
#                 "source_name": request.form.get("source_name"),
#                 "amount": request.form.get("amount"),
#                 "income_date": request.form.get("income_date") or date.today(),
#                 "description": request.form.get("description")
#             })
#             flash("Income recorded for selected society! ✅", "success")
#             return redirect(url_for("income.list_income"))
#         except Exception as e:
#             flash(f"Error: {str(e)}", "danger")

#     # Fetch all societies for the dropdown
#     societies = SocietyRepository.get_all()
#     return render_template("income/add.html", societies=societies)


from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from income.repository import IncomeRepository
from societies.repository import SocietyRepository 
from datetime import date

income_bp = Blueprint("income", __name__, url_prefix="/income")

# ======================================================
# 1. LIST INCOME RECORDS
# ======================================================
@income_bp.route("/")
@login_required
def list_income():
    user = session.get("user")
    role = user.get("role").lower()
    
    # 1. Logic for Super Admin (Filtering enabled)
    if role == "super_admin":
        # Get from URL dropdown selection, or show empty if none selected
        selected_soc_id = request.args.get("society_id")
        societies = SocietyRepository.get_all()
    # 2. Logic for Admin/Treasurer (Forced to their own society)
    else:
        selected_soc_id = session.get("society_id")
        societies = [] 

    records = IncomeRepository.get_by_society(selected_soc_id) if selected_soc_id else []

    return render_template("income/list.html", 
                           records=records, 
                           societies=societies, 
                           selected_soc=int(selected_soc_id) if selected_soc_id else None)


# ======================================================
# 2. ADD NEW INCOME (FIXED NULL ERROR)
# ======================================================

# @income_bp.route("/add", methods=["GET", "POST"])
# @login_required
# @role_required("treasurer", "super_admin")
# def add_income():
#     user = session.get("user")
#     role = user.get("role").lower()

#     if request.method == "POST":
#         # LOGIC: If Super Admin, get ID from dropdown. If Treasurer, get from Session.
#         if role == "super_admin":
#             target_society_id = request.form.get("society_id")
#         else:
#             target_society_id = session.get("society_id")

#         if not target_society_id:
#             flash("Error: Society ID is missing.", "danger")
#             return redirect(url_for("income.add_income"))

#         try:
#             IncomeRepository.add({
#                 "society_id": target_society_id, 
#                 "source_name": request.form.get("source_name"),
#                 "amount": request.form.get("amount"),
#                 "income_date": request.form.get("income_date") or date.today(),
#                 "description": request.form.get("description")
#             })
#             flash("Income recorded successfully! ✅", "success")
#             return redirect(url_for("income.list_income"))
#         except Exception as e:
#             flash(f"Database Error: {str(e)}", "danger")

#     # GET Logic: Only fetch societies for the dropdown if Super Admin
#     societies = SocietyRepository.get_all() if role == "super_admin" else []
    
#     return render_template("income/add.html", 
#                            societies=societies, 
#                            role=role)

# income/routes.py

@income_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "super_admin")
def add_income():
    user = session.get("user")
    role = user.get("role").lower()
    
    # Get society_id from URL (?society_id=X) or from Session (Treasurer)
    society_id = request.args.get("society_id") or session.get("society_id")

    if request.method == "POST":
        if not society_id:
            flash("Error: Society selection is required.", "danger")
            return redirect(url_for("income.list_income"))

        try:
            IncomeRepository.add({
                "society_id": society_id,
                "source_name": request.form.get("source_name"),
                "amount": request.form.get("amount"),
                "income_date": date.today(),
                "description": request.form.get("description")
            })
            flash("Income recorded successfully! ✅", "success")
            return redirect(url_for("income.list_income", society_id=society_id))
        except Exception as e:
            flash(f"Database Error: {str(e)}", "danger")

    return render_template("income/add.html", society_id=society_id)

