from flask import Blueprint, render_template, session, redirect, url_for, flash
from utils.decorators import login_required
from treasurers.service import TreasurerService
from reports.repository import ReportRepository

# REMOVE the url_prefix here to allow different root paths
dashboard_bp = Blueprint("dashboard", __name__)

# --- Helper to handle the common logic ---
def get_dashboard_data(role, society_id, user_id):
    stats = None
    super_stats = None
    owner_summary = None
    kpis = None

    if role == "super_admin":
        super_stats = TreasurerService.get_super_admin_stats()
        stats = TreasurerService.get_global_stats()
        kpis = ReportRepository.get_global_kpis()
    elif role in ["admin", "treasurer"] and society_id:
        stats = TreasurerService.get_finance_stats(society_id)
        kpis = ReportRepository.get_kpis(society_id)
    elif role in ["owner", "tenant"]:
        from owners.service import OwnerService
        owner_summary = OwnerService.get_owner_account_summary(user_id, role)
    
    return stats, super_stats, owner_summary, kpis

# --- ROLE SPECIFIC ROUTES ---

@dashboard_bp.route("/superadmin/dashboard/")
@login_required
def superadmin_index():
    if session["user"]["role"] != "super_admin":
        return redirect(url_for("dashboard.index_redirect")) # Security redirect
    
    stats, super_stats, owner_summary, kpis = get_dashboard_data("super_admin", None, None)
    return render_template("dashboard/index.html", stats=stats, super_stats=super_stats, kpis=kpis)

@dashboard_bp.route("/admin/dashboard/")
@login_required
def admin_index():
    if session["user"]["role"] != "admin":
        return redirect(url_for("dashboard.index_redirect"))
    
    stats, super_stats, owner_summary, kpis = get_dashboard_data("admin", session.get("society_id"), None)
    return render_template("dashboard/index.html", stats=stats, kpis=kpis)

@dashboard_bp.route("/treasurer/dashboard/")
@login_required
def treasurer_index():
    if session["user"]["role"] != "treasurer":
        return redirect(url_for("dashboard.index_redirect"))
    
    stats, super_stats, owner_summary, kpis = get_dashboard_data("treasurer", session.get("society_id"), None)
    return render_template("dashboard/index.html", stats=stats, kpis=kpis)

@dashboard_bp.route("/resident/dashboard/")
@login_required
def resident_index():
    user = session["user"]
    if user["role"] not in ["owner", "tenant"]:
        return redirect(url_for("dashboard.index_redirect"))
    
    stats, super_stats, owner_summary, kpis = get_dashboard_data(user["role"], None, user["id"])
    return render_template("dashboard/index.html", owner_summary=owner_summary)

# --- Fallback Redirection ---
@dashboard_bp.route("/dashboard/")
@login_required
def index_redirect():
    """Redirects the user to their specific URL if they visit the generic /dashboard/"""
    role = session["user"]["role"]
    if role == "super_admin": return redirect(url_for("dashboard.superadmin_index"))
    if role == "admin": return redirect(url_for("dashboard.admin_index"))
    if role == "treasurer": return redirect(url_for("dashboard.treasurer_index"))
    return redirect(url_for("dashboard.resident_index"))
