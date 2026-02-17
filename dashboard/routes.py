# # from flask import Blueprint, render_template, session
# # from utils.decorators import login_required

# # dashboard_bp = Blueprint(
# #     "dashboard",
# #     __name__,
# #     url_prefix="/dashboard"
# # )


# # @dashboard_bp.route("/")
# # @login_required
# # def index():
# #     user_name = session.get("user_name")
# #     return render_template("dashboard/index.html", user_name=user_name)


# # dashboard/routes.py
# from flask import Blueprint, render_template, session
# from utils.decorators import login_required
# from treasurers.service import TreasurerService # Import the service

# dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# @dashboard_bp.route("/")
# @login_required
# def index():
#     user = session.get("user")
#     role = user.get("role").lower()
#     society_id = session.get("society_id")
    
#     stats = None
#     # Only show financial cards to Admin and Treasurer
#     if role in ["admin", "treasurer"] and society_id:
#         stats = TreasurerService.get_finance_stats(society_id)

#     return render_template("dashboard/index.html", stats=stats)



from flask import Blueprint, render_template, session
from utils.decorators import login_required
from treasurers.service import TreasurerService

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# dashboard/routes.py

@dashboard_bp.route("/")
@login_required
def index():
    user = session.get("user")
    role = user.get("role").lower()
    society_id = session.get("society_id")
    
    stats = None
    super_stats = None
    owner_summary = None

    if role == "super_admin":
        # We ONLY fetch super_admin_stats (System-wide totals)
        # We do NOT fetch get_global_stats anymore
        super_stats = TreasurerService.get_super_admin_stats()
        
    elif role in ["admin", "treasurer"] and society_id:
        # Local Admin/Treasurer still sees their specific society stats
        stats = TreasurerService.get_finance_stats(society_id)
        
    elif role in ["owner", "tenant"]:
        from owners.service import OwnerService
        owner_summary = OwnerService.get_owner_account_summary(user["id"], role)

    return render_template("dashboard/index.html", 
                           stats=stats, 
                           super_stats=super_stats, 
                           owner_summary=owner_summary)