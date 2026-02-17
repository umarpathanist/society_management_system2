from flask import Blueprint, render_template
from utils.decorators import login_required, permission_required

payments_bp = Blueprint(
    "payments",
    __name__,
    url_prefix="/payments"
)


@payments_bp.route("/collect")
@login_required
@permission_required("collect_payments")
def collect_payment():
    return render_template("payments/collect.html")
