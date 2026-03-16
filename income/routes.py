from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from income.repository import IncomeRepository
from societies.repository import SocietyRepository
from datetime import date

income_bp = Blueprint("income", __name__, url_prefix="/income")

@income_bp.route("/")
@login_required
def list_income():
    """Fetches the unified ledger for the society."""
    user = session.get("user")
    role = user.get("role").lower()
    
    # Identify which society to filter by
    selected_soc_id = request.args.get("society_id") if role == "super_admin" else session.get("society_id")

    # FIX: Call the exact method name defined in repository
    records = IncomeRepository.get_combined_ledger(selected_soc_id) if selected_soc_id else []
    
    # Load societies for Super Admin dropdown
    from societies.repository import SocietyRepository
    societies = SocietyRepository.get_all() if role == "super_admin" else []

    return render_template("income/list.html", 
                           records=records, 
                           societies=societies, 
                           selected_soc=selected_soc_id,
                           role=role)

@income_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "super_admin")
def add_income():
    user = session.get("user")
    role = user.get("role").lower()

    if request.method == "POST":
        # Role logic to determine ID
        target_id = request.form.get("society_id") if role == "super_admin" else session.get("society_id")
        
        try:
            IncomeRepository.add({
                "society_id": int(target_id),
                "source_name": request.form.get("source_name"),
                "amount": float(request.form.get("amount") or 0),
                "income_date": request.form.get("income_date") or date.today(),
                "description": request.form.get("description")
            })
            flash("Income record saved successfully! ✅", "success")
            return redirect(url_for("income.list_income", society_id=target_id))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    # Determine building info for the UI
    current_soc_id = request.args.get("society_id") or session.get("society_id")
    soc_name = "Society HQ"
    if current_soc_id:
        soc_details = SocietyRepository.get_by_id(current_soc_id)
        if soc_details: soc_name = soc_details['name']

    return render_template("income/add.html", 
                           society_id=current_soc_id, 
                           society_name=soc_name,
                           role=role)
