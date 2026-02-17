from flask import Blueprint, render_template
from utils.decorators import login_required

tenants_bp = Blueprint("tenants", __name__, url_prefix="/tenants")

@tenants_bp.route("/")
@login_required
def list_tenants():
    return render_template("tenants/list.html")
