from flask import Blueprint, render_template
from utils.decorators import login_required, role_required, permission_required


maintenance_bp = Blueprint(
    "maintenance",
    __name__,
    url_prefix="/maintenance"
)


# -------------------------------------------------
# MAINTENANCE DASHBOARD (admin / treasurer)
# -------------------------------------------------
@maintenance_bp.route("/")
@login_required
@permission_required("view_maintenance")
def maintenance_dashboard():
    return render_template("maintenance/dashboard.html")
