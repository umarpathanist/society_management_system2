# reports/routes.py
from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from reports.repository import ReportRepository

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
@login_required
@role_required("admin", "treasurer")
def index():
    soc_id = session.get("society_id")
    if not soc_id: return "Access Denied: No Society Context"

    # Fetch data for all modules
    finance = ReportRepository.get_financial_summary(soc_id)
    ledger = ReportRepository.get_unified_ledger(soc_id)
    dues = ReportRepository.get_outstanding_dues(soc_id)

    return render_template("reports/index.html", 
                           finance=finance, 
                           ledger=ledger, 
                           dues=dues)