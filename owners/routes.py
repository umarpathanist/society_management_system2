# from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# from utils.decorators import login_required, role_required
# from owners.service import OwnerService
# from owners.repository import OwnerRepository

# owners_bp = Blueprint("owners", __name__, url_prefix="/owners")

# # owners/routes.py

# @owners_bp.route("/list")
# @login_required
# @role_required("admin", "super_admin")
# def list_owners():
#     current_user = session.get("user")
#     user_role = current_user.get("role").lower()
#     society_id = session.get("society_id")

#     # LOGIC: 
#     # Super Admin -> target_soc is None (Repository will show ALL societies)
#     # Admin -> target_soc is an ID (Repository will filter by that society)
#     target_soc = None if user_role == "super_admin" else society_id
    
#     # Security check for regular admins
#     if user_role == "admin" and not society_id:
#         flash("No society assigned to your account. Contact Super Admin.", "warning")
#         return render_template("owners/list.html", users=[])

#     users_list = OwnerRepository.get_users_by_society_and_roles(
#         society_id=target_soc,
#         roles=("owner", "tenant")
#     )

#     return render_template("owners/list.html", users=users_list)

# @owners_bp.route("/add", methods=["GET", "POST"])
# @login_required
# @role_required("admin", "super_admin")
# def add_owner():
#     if request.method == "POST":
#         try:
#             OwnerService.create_owner_or_tenant({
#                 "full_name": request.form.get("full_name"),
#                 "email": request.form.get("email"),
#                 "role": request.form.get("role"),
#                 "society_id": session.get("society_id")
#             })
#             flash("User added successfully!", "success")
#             return redirect(url_for("owners.list_owners"))
#         except Exception as e:
#             flash(f"Error: {str(e)}", "danger")
#     return render_template("owners/add.html")

# # owners/routes.py

# @owners_bp.route("/my-flat")
# @login_required
# @role_required("owner", "tenant")
# def my_flat():
#     user = session["user"]
#     # Get the consolidated summary instead of just a list of flats
#     summary = OwnerService.get_owner_account_summary(user["id"], user["role"])
    
#     return render_template("owners/my_flat.html", summary=summary)

# @owners_bp.route("/my-maintenance")
# @login_required
# @role_required("owner", "tenant")
# def my_maintenance():
#     user = session["user"]
#     maintenance = OwnerService.get_my_maintenance(user["id"], user["role"])
#     return render_template("owners/my_maintenance.html", maintenance=maintenance)


# # owners/routes.py
# from maintenance.repository import MaintenanceRepository # Ensure this is imported

# @owners_bp.route("/pay/<int:maintenance_id>", methods=["POST"])
# @login_required
# @role_required("owner", "tenant")
# def pay_bill(maintenance_id):
#     try:
#         # Check if bill exists
#         bill = MaintenanceRepository.get_bill_by_id(maintenance_id)
#         if not bill:
#             flash("Bill not found.", "danger")
#             return redirect(url_for("owners.my_maintenance"))

#         # We simulate a successful payment here
#         MaintenanceRepository.mark_as_paid(
#             maintenance_id=maintenance_id,
#             method='Online',
#             receiver_id=None # Self-paid by owner
#         )
#         flash("Payment successful! The entry is now visible in the Ledger. ✅", "success")
#     except Exception as e:
#         flash(f"Payment Error: {str(e)}", "danger")
        
#     return redirect(url_for("owners.my_maintenance"))


# @owners_bp.route("/edit/<int:id>", methods=["GET", "POST"])
# @login_required
# @role_required("admin", "super_admin")
# def edit_owner(id):
#     user_to_edit = OwnerService.get_user_details(id)
#     if not user_to_edit:
#         flash("User not found", "danger")
#         return redirect(url_for("owners.list_owners"))

#     if request.method == "POST":
#         try:
#             OwnerService.update_user(id, {
#                 "full_name": request.form.get("full_name"),
#                 "email": request.form.get("email"),
#                 "role": request.form.get("role")
#             })
#             flash("User updated successfully!", "success")
#             return redirect(url_for("owners.list_owners"))
#         except Exception as e:
#             flash(f"Error: {str(e)}", "danger")

#     return render_template("owners/edit.html", user=user_to_edit)

# @owners_bp.route("/delete/<int:id>", methods=["POST"])
# @login_required
# @role_required("admin", "super_admin")
# def delete_owner(id):
#     try:
#         OwnerService.delete_user(id)
#         flash("User removed successfully!", "success")
#     except Exception as e:
#         flash(f"Error: {str(e)}", "danger")
#     return redirect(url_for("owners.list_owners"))

# # owners/routes.py

# @owners_bp.route("/checkout/<int:maintenance_id>")
# @login_required
# @role_required("owner", "tenant", "treasurer", "admin") 
# def checkout(maintenance_id):
#     """
#     Renders a payment confirmation page with bill details pre-filled.
#     """
#     from maintenance.repository import MaintenanceRepository
    
#     # Fetch specific bill details
#     bill = MaintenanceRepository.get_by_id_with_flat(maintenance_id)
    
#     if not bill:
#         flash("Maintenance record not found.", "danger")
#         return redirect(url_for("owners.my_maintenance"))
        
#     return render_template("owners/checkout.html", bill=bill)




# @owners_bp.route("/process-payment/<int:maintenance_id>", methods=["POST"])
# @login_required
# @role_required("owner", "tenant", "treasurer", "admin") 
# def process_payment(maintenance_id):
#     """
#     Called when the resident clicks 'Confirm & Pay Now'.
#     """
#     try:
#         from maintenance.repository import MaintenanceRepository
        
#         # This now sets the date, which triggers the report visibility
#         MaintenanceRepository.mark_as_paid(maintenance_id)
        
#         flash("Payment Successful! Your record is now visible in the society ledger. ✅", "success")
#     except Exception as e:
#         flash(f"Payment failed: {str(e)}", "danger")
        
#     return redirect(url_for("owners.my_maintenance"))

# from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
# import razorpay
# from extensions import get_razorpay_client
# from maintenance.repository import MaintenanceRepository
# from utils.decorators import login_required, role_required

# # owners/routes.py

# @owners_bp.route("/create-payment-order/<int:maintenance_id>", methods=["POST"])
# @login_required
# def create_payment_order(maintenance_id):
#     from maintenance.repository import MaintenanceRepository
    
#     try:
#         # 1. Get the bill details
#         bill = MaintenanceRepository.get_bill_by_id(maintenance_id)
#         if not bill:
#             return jsonify({"error": "Bill not found"}), 404

#         # 2. Get Razorpay Client
#         client = get_razorpay_client()

#         # 3. Prepare Order Data (Amount must be an integer in Paise)
#         # ₹1500.00 -> 150000 paise
#         amount_in_paise = int(float(bill['amount']) * 100)

#         data = {
#             "amount": amount_in_paise,
#             "currency": "INR",
#             "receipt": f"order_rcpt_{maintenance_id}",
#             "notes": {
#                 "bill_id": maintenance_id,
#                 "resident": session['user']['full_name']
#             }
#         }
        
#         # 4. Create Order on Razorpay
#         order = client.order.create(data=data)
        
#         # 5. Save the Order ID to our Database
#         # Note: If this line crashes, ensure you ran the SQL in Step 1 above!
#         MaintenanceRepository.save_order_id(maintenance_id, order['id'])

#         # 6. Return JSON to the Frontend
#         return jsonify({
#             "id": order['id'],
#             "amount": order['amount'],
#             "key": current_app.config['RAZORPAY_KEY_ID'],
#             "full_name": session['user']['full_name'],
#             "email": session['user']['email']
#         })

#     except Exception as e:
#         # Check your terminal (VS Code black screen) for this output
#         print(f"--- RAZORPAY DEBUG ERROR ---")
#         print(f"Error Message: {str(e)}")
#         print(f"----------------------------")
#         return jsonify({"error": f"Gateway Error: {str(e)}"}), 500    

# @owners_bp.route("/verify-payment", methods=["POST"])
# @login_required
# def verify_payment():
#     data = request.get_json()
#     client = get_razorpay_client()
    
#     try:
#         # 1. Verify Signature
#         client.utility.verify_payment_signature({
#             'razorpay_order_id': data['razorpay_order_id'],
#             'razorpay_payment_id': data['razorpay_payment_id'],
#             'razorpay_signature': data['razorpay_signature']
#         })
        
#         # 2. Update DB
#         MaintenanceRepository.complete_payment(
#             data['bill_id'], 
#             data['razorpay_payment_id'], 
#             data['razorpay_signature']
#         )
        
#         return jsonify({"status": "ok"})
#     except Exception as e:
#         print(f"VERIFICATION FAILED: {e}")
#         return jsonify({"status": "failed", "error": str(e)}), 400






from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from utils.decorators import login_required, role_required
from owners.service import OwnerService
from owners.repository import OwnerRepository
from maintenance.repository import MaintenanceRepository
import razorpay

owners_bp = Blueprint("owners", __name__, url_prefix="/owners")

# ---------------------------------------------------------
# 1. ADMIN LOGIC: LIST OWNERS & TENANTS (FIXES THE BUILDERROR)
# ---------------------------------------------------------
@owners_bp.route("/list")
@login_required
@role_required("admin", "super_admin")
def list_owners():
    """Fetches all residents for the admin list view."""
    user = session.get("user")
    user_role = user.get("role").lower()
    society_id = session.get("society_id")

    # Super Admin sees everyone, local Admin sees only their society
    target_soc = None if user_role == "super_admin" else society_id
    
    users_list = OwnerRepository.get_users_by_society_and_roles(target_soc, ("owner", "tenant"))
    return render_template("owners/list.html", users=users_list)


# ---------------------------------------------------------
# 2. RESIDENT LOGIC: DASHBOARD & DUES
# ---------------------------------------------------------
@owners_bp.route("/my-flat")
@login_required
@role_required("owner", "tenant")
def my_flat():
    user = session["user"]
    summary = OwnerService.get_owner_account_summary(user["id"], user["role"])
    return render_template("owners/my_flat.html", summary=summary)

@owners_bp.route("/my-maintenance")
@login_required
@role_required("owner", "tenant")
def my_maintenance():
    user = session["user"]
    maintenance = OwnerService.get_my_maintenance(user["id"], user["role"])
    return render_template("owners/my_maintenance.html", maintenance=maintenance)


# ---------------------------------------------------------
# 3. RAZORPAY PAYMENT LOGIC
# ---------------------------------------------------------
@owners_bp.route("/create-order/<int:bill_id>", methods=["POST"])
@login_required
def create_order(bill_id):
    bill = MaintenanceRepository.get_bill_by_id(bill_id)
    if not bill:
        return jsonify({"status": "error", "message": "Bill not found"}), 404

    try:
        client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'], 
            current_app.config['RAZORPAY_KEY_SECRET']
        ))
        amount_paise = int(float(bill['amount']) * 100)
        
        order = client.order.create(data={
            "amount": amount_paise, "currency": "INR",
            "receipt": f"bill_{bill_id}", "payment_capture": 1
        })
        
        MaintenanceRepository.save_order_id(bill_id, order['id'])
        
        return jsonify({
            "status": "success",
            "order_id": order['id'],
            "amount": order['amount'],
            "key": current_app.config['RAZORPAY_KEY_ID'],
            "full_name": session['user']['full_name'],
            "email": session['user']['email']
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@owners_bp.route("/verify-payment", methods=["POST"])
@login_required
def verify_payment():
    data = request.get_json()
    try:
        client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'], 
            current_app.config['RAZORPAY_KEY_SECRET']
        ))
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        MaintenanceRepository.complete_payment(data['bill_id'], data['razorpay_payment_id'], data['razorpay_signature'])
        return jsonify({"status": "success"})
    except Exception:
        return jsonify({"status": "error", "message": "Verification failed"}), 400


# ---------------------------------------------------------
# 4. CRUD: ADD, EDIT, DELETE
# ---------------------------------------------------------
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

@owners_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def edit_owner(id):
    user_to_edit = OwnerService.get_user_details(id)
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
    OwnerService.delete_user(id)
    flash("User removed successfully.", "success")
    return redirect(url_for("owners.list_owners"))

@owners_bp.route("/pay/<int:maintenance_id>", methods=["POST"])
@login_required
@role_required("owner", "tenant")
def pay_bill(maintenance_id):
    # Standard manual simulation for owners
    MaintenanceRepository.mark_as_paid(maintenance_id, method='Online')
    flash("Payment recorded successfully!", "success")
    return redirect(url_for("owners.my_maintenance"))