# from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# from utils.decorators import login_required, role_required
# from admin.service import AdminService
# from societies.repository import SocietyRepository

# admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# @admin_bp.route("/admins")
# @login_required
# @role_required("super_admin")
# def list_admins():
#     admins = AdminService.get_admins()
#     return render_template("admin/list_admins.html", admins=admins)

# # admin/routes.py

# @admin_bp.route("/admins/add", methods=["GET", "POST"])
# @login_required
# @role_required("super_admin")
# def add_admin():
#     if request.method == "POST":
#         # Capture form data
#         form_data = {
#             "full_name": request.form.get("full_name"),
#             "email": request.form.get("email"),
#             "password": request.form.get("password"),
#             "society_id": request.form.get("society_id")
#         }
        
#         try:
#             AdminService.create_admin(form_data)
#             flash("Admin created and credentials emailed! ✅", "success")
#             return redirect(url_for("admin.list_admins"))
#         except ValueError as e:
#             # Shows the "Already Managed By" error
#             flash(str(e), "warning")
#         except Exception as e:
#             # Shows system errors
#             flash(f"System Error: {str(e)}", "danger")

#     societies = SocietyRepository.get_all()
#     return render_template("admin/add.html", societies=societies)



# @admin_bp.route("/admins/<int:user_id>/edit", methods=["GET", "POST"])
# @login_required
# @role_required("super_admin")
# def edit_admin(user_id):
#     admin = AdminService.get_by_id(user_id)
#     if request.method == "POST":
#         AdminService.update_admin(user_id, request.form)
#         flash("Admin details updated! ✅", "success")
#         return redirect(url_for("admin.list_admins"))
#     return render_template("admin/edit.html", admin=admin)

# @admin_bp.route("/admins/<int:user_id>/delete", methods=["POST"])
# @login_required
# @role_required("super_admin")
# def delete_admin(user_id):
#     AdminService.delete_admin(user_id)
#     flash("Admin removed from system.", "success")
#     return redirect(url_for("admin.list_admins"))


# # admin/routes.py

# @admin_bp.route("/admins/<int:admin_id>/assign", methods=["GET", "POST"])
# @login_required
# @role_required("super_admin")
# def assign_society(admin_id):
#     admin = AdminService.get_by_id(admin_id)
#     if request.method == "POST":
#         society_id = request.form.get("society_id")
#         try:
#             # This will trigger the check in the service
#             AdminService.assign_society(admin_id, society_id)
#             flash(f"Society assigned to {admin['full_name']}! ✅", "success")
#             return redirect(url_for("admin.list_admins"))
#         except ValueError as e:
#             # This flashes the "Already Managed By..." error
#             flash(str(e), "danger")
#             return redirect(url_for("admin.assign_society", admin_id=admin_id))

#     # GET Logic...




from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from admin.service import AdminService
from societies.repository import SocietyRepository

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 1. LIST ADMINS
@admin_bp.route("/admins")
@login_required
@role_required("super_admin")
def list_admins():
    admins = AdminService.get_admins()
    return render_template("admin/list_admins.html", admins=admins)

# 2. ADD NEW ADMIN
@admin_bp.route("/admins/add", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def add_admin():
    if request.method == "POST":
        form_data = {
            "full_name": request.form.get("full_name"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
            "society_id": request.form.get("society_id")
        }
        
        try:
            AdminService.create_admin(form_data)
            flash("Admin created and credentials emailed! ✅", "success")
            return redirect(url_for("admin.list_admins"))
        except ValueError as e:
            flash(str(e), "warning")
        except Exception as e:
            flash(f"System Error: {str(e)}", "danger")

    societies = SocietyRepository.get_all()
    return render_template("admin/add.html", societies=societies)

# 3. EDIT ADMIN
@admin_bp.route("/admins/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def edit_admin(user_id):
    admin = AdminService.get_by_id(user_id)
    if request.method == "POST":
        AdminService.update_admin(user_id, request.form)
        flash("Admin details updated! ✅", "success")
        return redirect(url_for("admin.list_admins"))
    return render_template("admin/edit.html", admin=admin)

# 4. DELETE ADMIN
@admin_bp.route("/admins/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("super_admin")
def delete_admin(user_id):
    AdminService.delete_admin(user_id)
    flash("Admin removed from system.", "success")
    return redirect(url_for("admin.list_admins"))

# 5. ASSIGN SOCIETY (FIXED)
@admin_bp.route("/admins/<int:admin_id>/assign", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def assign_society(admin_id):
    # Fetch admin to ensure they exist
    admin = AdminService.get_by_id(admin_id)
    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for("admin.list_admins"))

    if request.method == "POST":
        society_id = request.form.get("society_id")
        try:
            # Service performs the "One Admin per Society" check
            AdminService.assign_society(admin_id, society_id)
            flash(f"Society assigned to {admin['full_name']}! ✅", "success")
            return redirect(url_for("admin.list_admins"))
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("admin.assign_society", admin_id=admin_id))
        except Exception as e:
            flash(f"System Error: {str(e)}", "danger")
            return redirect(url_for("admin.assign_society", admin_id=admin_id))

    # --- THE FIX WAS HERE ---
    # GET logic: Fetch all societies for the dropdown and show the form
    societies = SocietyRepository.get_all()
    return render_template("admin/assign_society.html", admin=admin, societies=societies)