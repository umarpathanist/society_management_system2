from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from owners.service import OwnerService
from owners.repository import OwnerRepository

owners_bp = Blueprint("owners", __name__, url_prefix="/owners")

# owners/routes.py

@owners_bp.route("/list")
@login_required
@role_required("admin", "super_admin")
def list_owners():
    current_user = session.get("user")
    user_role = current_user.get("role").lower()
    society_id = session.get("society_id")

    # LOGIC: 
    # Super Admin -> target_soc is None (Repository will show ALL societies)
    # Admin -> target_soc is an ID (Repository will filter by that society)
    target_soc = None if user_role == "super_admin" else society_id
    
    # Security check for regular admins
    if user_role == "admin" and not society_id:
        flash("No society assigned to your account. Contact Super Admin.", "warning")
        return render_template("owners/list.html", users=[])

    users_list = OwnerRepository.get_users_by_society_and_roles(
        society_id=target_soc,
        roles=("owner", "tenant")
    )

    return render_template("owners/list.html", users=users_list)

@owners_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def add_owner():
    if request.method == "POST":
        try:
            OwnerService.create_owner_or_tenant({
                "full_name": request.form.get("full_name"),
                "email": request.form.get("email"),
                "role": request.form.get("role"),
                "society_id": session.get("society_id")
            })
            flash("User added successfully!", "success")
            return redirect(url_for("owners.list_owners"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
    return render_template("owners/add.html")

# owners/routes.py

@owners_bp.route("/my-flat")
@login_required
@role_required("owner", "tenant")
def my_flat():
    user = session["user"]
    # Get the consolidated summary instead of just a list of flats
    summary = OwnerService.get_owner_account_summary(user["id"], user["role"])
    
    return render_template("owners/my_flat.html", summary=summary)

@owners_bp.route("/my-maintenance")
@login_required
@role_required("owner", "tenant")
def my_maintenance():
    user = session["user"]
    maintenance = OwnerService.get_my_maintenance(user["id"], user["role"])
    return render_template("owners/my_maintenance.html", maintenance=maintenance)


# owners/routes.py
from maintenance.repository import MaintenanceRepository # Ensure this is imported

# @owners_bp.route("/pay/<int:maintenance_id>", methods=["POST"])
# @login_required
# @role_required("owner", "tenant")
# def pay_bill(maintenance_id):
#     try:
#         # Update the status in DB
#         MaintenanceRepository.mark_as_paid(maintenance_id)
        
#         flash("Payment successful! Your bill has been marked as Paid. ✅", "success")
#     except Exception as e:
#         flash(f"Error processing payment: {str(e)}", "danger")
        
#     return redirect(url_for("owners.my_maintenance"))
# owners/routes.py

@owners_bp.route("/pay/<int:maintenance_id>", methods=["POST"])
@login_required
# FIXED: Added 'treasurer' and 'admin' so they can also process payments
@role_required("owner", "tenant", "treasurer", "admin")
def pay_bill(maintenance_id):
    try:
        from maintenance.repository import MaintenanceRepository
        
        # 1. Update the status in the database
        MaintenanceRepository.mark_as_paid(maintenance_id)
        flash("Payment recorded successfully! ✅", "success")

        # 2. SMART REDIRECT
        # If a Treasurer paid, send them back to the Reports Hub
        # If an Owner paid, send them back to their Dues page
        user_role = session["user"]["role"].lower()
        if user_role in ['treasurer', 'admin']:
            return redirect(url_for("reports.index"))
        else:
            return redirect(url_for("owners.my_maintenance"))

    except Exception as e:
        flash(f"Error processing payment: {str(e)}", "danger")
        return redirect(request.referrer)

# owners/routes.py

@owners_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def edit_owner(id):
    user_to_edit = OwnerService.get_user_details(id)
    if not user_to_edit:
        flash("User not found", "danger")
        return redirect(url_for("owners.list_owners"))

    if request.method == "POST":
        try:
            OwnerService.update_user(id, {
                "full_name": request.form.get("full_name"),
                "email": request.form.get("email"),
                "role": request.form.get("role")
            })
            flash("User updated successfully!", "success")
            return redirect(url_for("owners.list_owners"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("owners/edit.html", user=user_to_edit)

@owners_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def delete_owner(id):
    try:
        OwnerService.delete_user(id)
        flash("User removed successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("owners.list_owners"))

# owners/routes.py

@owners_bp.route("/checkout/<int:maintenance_id>")
@login_required
@role_required("owner", "tenant", "treasurer", "admin") 
def checkout(maintenance_id):
    """
    Renders a payment confirmation page with bill details pre-filled.
    """
    from maintenance.repository import MaintenanceRepository
    
    # Fetch specific bill details
    bill = MaintenanceRepository.get_by_id_with_flat(maintenance_id)
    
    if not bill:
        flash("Maintenance record not found.", "danger")
        return redirect(url_for("owners.my_maintenance"))
        
    return render_template("owners/checkout.html", bill=bill)




@owners_bp.route("/process-payment/<int:maintenance_id>", methods=["POST"])
@login_required
@role_required("owner", "tenant", "treasurer", "admin") 
def process_payment(maintenance_id):
    """
    Called when the resident clicks 'Confirm & Pay Now'.
    """
    try:
        from maintenance.repository import MaintenanceRepository
        
        # This now sets the date, which triggers the report visibility
        MaintenanceRepository.mark_as_paid(maintenance_id)
        
        flash("Payment Successful! Your record is now visible in the society ledger. ✅", "success")
    except Exception as e:
        flash(f"Payment failed: {str(e)}", "danger")
        
    return redirect(url_for("owners.my_maintenance"))