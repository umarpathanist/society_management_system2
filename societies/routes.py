from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from societies.repository import SocietyRepository

societies_bp = Blueprint("societies", __name__, url_prefix="/societies")

# ---------------------------------------------------------
# 1. LIST SOCIETIES
# ---------------------------------------------------------
@societies_bp.route("/")
@login_required
def list_societies():
    user = session.get("user")
    role = user.get("role").lower()
    society_id = session.get("society_id")

    if role == "super_admin":
        # Super Admin sees everything
        societies = SocietyRepository.get_all()
    else:
        # Admin only sees their assigned society
        societies = SocietyRepository.get_by_admin(society_id)

    return render_template("societies/list.html", societies=societies)

# ---------------------------------------------------------
# 2. ADD SOCIETY
# ---------------------------------------------------------
# societies/routes.py

@societies_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def add_society():
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "address": request.form.get("address"),
            "total_blocks": request.form.get("total_blocks"),
            "floors_per_block": request.form.get("floors_per_block"), # Synchronized
            "flats_per_floor": request.form.get("flats_per_floor")    # Synchronized
        }

        try:
            SocietyRepository.create(data)
            flash("Society and all its units generated successfully! ✅", "success")
            return redirect(url_for("societies.list_societies"))
        except Exception as e:
            flash(f"Error creating society: {str(e)}", "danger")

    return render_template("societies/add.html")



# ---------------------------------------------------------
# 3. EDIT SOCIETY
# ---------------------------------------------------------
@societies_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def edit_society(id):
    society = SocietyRepository.get_by_id(id)
    if request.method == "POST":
        try:
            # Capture ALL fields from the form
            update_data = {
                "name": request.form.get("name"),
                "address": request.form.get("address"),
                "total_blocks": request.form.get("total_blocks"),
                "floors_per_block": request.form.get("floors_per_block"),
                "flats_per_floor": request.form.get("flats_per_floor")
            }
            SocietyRepository.update(id, update_data)
            flash("Society updated and structure generated! ✅", "success")
            return redirect(url_for("societies.list_societies"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
    return render_template("societies/edit.html", society=society)

# ---------------------------------------------------------
# 4. DELETE SOCIETY
# ---------------------------------------------------------
@societies_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
@role_required("super_admin")
def delete_society(id):
    try:
        SocietyRepository.delete(id)
        flash("Society removed successfully.", "success")
    except Exception as e:
        flash(f"Delete Error: {str(e)}", "danger")
    
    return redirect(url_for("societies.list_societies"))  

