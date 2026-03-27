from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from expenses.repository import ExpenseRepository
from societies.repository import SocietyRepository
from utils.decorators import login_required, role_required
from datetime import date

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")

# ======================================================
# 1. LIST EXPENSES (Matches url_for('expenses.list_expenses'))
# ======================================================
@expenses_bp.route("/")
@login_required
def list_expenses():
    user = session.get("user")
    role = user.get("role").lower()
    
    # Logic: Super Admin filters by URL, Treasurer/Admin uses their session
    if role == "super_admin":
        selected_soc_id = request.args.get("society_id")
        societies = SocietyRepository.get_all()
    else:
        selected_soc_id = session.get("society_id")
        societies = []

    records = ExpenseRepository.get_by_society(selected_soc_id) if selected_soc_id else []

    return render_template("expenses/list.html", 
                           records=records, 
                           societies=societies, 
                           selected_soc=int(selected_soc_id) if selected_soc_id else None,
                           role=role)


# ======================================================
# 2. ADD EXPENSE (Matches url_for('expenses.add_expense'))
# ======================================================
@expenses_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("super_admin", "admin", "treasurer")
def add_expense():
    user = session.get("user")
    role = user.get("role").lower()

    if request.method == "POST":
        # ✅ FIXED: Get society_id from form, fallback to session
        society_id = request.form.get("society_id") or session.get("society_id")

        if not society_id:
            flash("Society association missing.", "danger")
            return redirect(url_for("expenses.add_expense"))

        try:
            ExpenseRepository.add({
                "society_id": int(society_id),  # ✅ Convert to int
                "category": request.form.get("category"),
                "amount": request.form.get("amount"),
                "expense_date": request.form.get("expense_date") or str(date.today()),
                "description": request.form.get("description")
            })
            flash("Expense recorded successfully! ✅", "success")
            return redirect(url_for("expenses.list_expenses", society_id=society_id))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    # GET: Get society_id from URL or session
    target_soc_id = request.args.get("society_id") or session.get("society_id")

    soc_data = SocietyRepository.get_by_id(target_soc_id) if target_soc_id else None
    society_name = soc_data['name'] if soc_data else "Unknown Society"

    return render_template("expenses/add.html",
                           target_soc_id=target_soc_id,
                           society_name=society_name,
                           role=role)