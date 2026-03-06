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
import razorpay
from flask import Blueprint, request, jsonify, session, current_app
from maintenance.repository import MaintenanceRepository
from utils.pdf_helper import generate_pdf_blob
from utils.mail import send_email_with_pdf
from datetime import datetime

# --- 1. CREATE RAZORPAY ORDER ---
# @owners_bp.route("/create-payment-order/<int:bill_id>", methods=["POST"])
# @login_required
# def create_payment_order(bill_id):
#     bill = MaintenanceRepository.get_full_invoice_data(bill_id)
#     if not bill:
#         return jsonify({"status": "error", "message": "Bill not found"}), 404

#     try:
#         client = razorpay.Client(auth=(
#             current_app.config['RAZORPAY_KEY_ID'], 
#             current_app.config['RAZORPAY_KEY_SECRET']
#         ))
        
#         amount_paise = int(float(bill['amount']) * 100)
        
#         # Create Razorpay Order
#         order = client.order.create(data={
#             "amount": amount_paise, "currency": "INR",
#             "receipt": f"bill_{bill_id}"
#         })
        
#         # Save order ID in DB for verification
#         MaintenanceRepository.save_order_id(bill_id, order['id'])
        
#         return jsonify({
#             "status": "success",
#             "order_id": order['id'],
#             "amount": order['amount'],
#             "key": current_app.config['RAZORPAY_KEY_ID'],
#             "full_name": session['user']['full_name'],
#             "email": session['user']['email']
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

# # --- 2. VERIFY PAYMENT SIGNATURE ---
# @owners_bp.route("/verify-payment", methods=["POST"])
# @login_required
# def verify_payment():
#     data = request.get_json()
#     try:
#         client = razorpay.Client(auth=(
#             current_app.config['RAZORPAY_KEY_ID'], 
#             current_app.config['RAZORPAY_KEY_SECRET']
#         ))
        
#         # Verify Razorpay Signature
#         client.utility.verify_payment_signature({
#             'razorpay_order_id': data['razorpay_order_id'],
#             'razorpay_payment_id': data['razorpay_payment_id'],
#             'razorpay_signature': data['razorpay_signature']
#         })

#         # Update DB and trigger PDF/Email
#         bill_id = data['bill_id']
#         MaintenanceRepository.mark_as_paid(bill_id, method='Razorpay Online', p_id=data['razorpay_payment_id'])
        
#         # Generate and Email Invoice (Milestone C)
#         invoice_data = MaintenanceRepository.get_full_invoice_data(bill_id)
#         context = {"society": {"name": invoice_data['society_name'], "address": invoice_data['society_address']},
#                    "user": {"full_name": invoice_data['owner_name']}, "flat": {"flat_number": invoice_data['flat_number']},
#                    "maintenance": invoice_data, "date_today": datetime.now().strftime('%B %d, %Y')}
        
#         pdf = generate_pdf_blob('maintenance/invoice_template.html', context)
#         send_email_with_pdf(invoice_data['owner_email'], invoice_data['owner_name'], pdf, f"Receipt_{bill_id}.pdf", invoice_data)

#         # Notify the treasurer
#         treasurer = TreasurerRepository.get_treasurer_by_society(invoice_data['society_id'])
#         if treasurer:
#             payment_date = datetime.now().strftime("%d-%m-%Y")
#             NotificationRepository.create(
#                 user_id=treasurer['id'],
#                 title="Payment Received 💰",
#                 message=f"Flat {invoice_data['flat_number']} has paid ₹{invoice_data['amount']} for {invoice_data['month']} on {payment_date}.",
#                 notif_type="finance"
#             )

#         return jsonify({"status": "success"})
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400


from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from utils.decorators import login_required, role_required
from maintenance.repository import MaintenanceRepository
from treasurers.repository import TreasurerRepository
from notifications.repository import NotificationRepository
from utils.pdf_helper import generate_pdf_blob 
from utils.mail import send_email_with_pdf
import razorpay
from datetime import datetime

# --- 1. CREATE PAYMENT ORDER ---
@owners_bp.route("/create-payment-order/<int:bill_id>", methods=["POST"])
@login_required
def create_payment_order(bill_id):
    # Fetch full data to ensure we have the correct amount and recipient info
    bill = MaintenanceRepository.get_full_invoice_data(bill_id)
    if not bill:
        return jsonify({"status": "error", "message": "Bill not found"}), 404

    try:
        client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'], 
            current_app.config['RAZORPAY_KEY_SECRET']
        ))
        
        amount_paise = int(float(bill['amount']) * 100)
        
        # Create Razorpay Order
        order = client.order.create(data={
            "amount": amount_paise, 
            "currency": "INR",
            "receipt": f"bill_{bill_id}"
        })
        
        # Save order ID in DB for verification later
        MaintenanceRepository.save_order_id(bill_id, order['id'])
        
        # Pass the dynamic recipient info to the frontend checkout
        return jsonify({
            "status": "success",
            "order_id": order['id'],
            "amount": order['amount'],
            "key": current_app.config['RAZORPAY_KEY_ID'],
            "full_name": bill['recipient_name'], # Correct name for Owner OR Tenant
            "email": bill['recipient_email']      # Correct email for Owner OR Tenant
        })
    except Exception as e:
        print(f"ORDER CREATION ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 2. VERIFY PAYMENT SIGNATURE ---
@owners_bp.route("/verify-payment", methods=["POST"])
@login_required
def verify_payment():
    data = request.get_json()
    try:
        client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'], 
            current_app.config['RAZORPAY_KEY_SECRET']
        ))
        
        # 1. Verify Razorpay Signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        bill_id = data['bill_id']
        # 2. Mark as Paid in DB
        MaintenanceRepository.mark_as_paid(bill_id, method='Razorpay Online', p_id=data['razorpay_payment_id'])
        
        # 3. Fetch Full Data (Using the fixed Repo method)
        invoice_data = MaintenanceRepository.get_full_invoice_data(bill_id)

        # 4. Prepare Context for PDF (Use recipient_name)
        context = {
            "society": {"name": invoice_data['society_name'], "address": invoice_data['society_address']},
            "user": {"full_name": invoice_data['recipient_name'], "email": invoice_data['recipient_email']}, 
            "flat": {"flat_number": invoice_data['flat_number'], "block_name": invoice_data['block_name']},
            "maintenance": invoice_data, 
            "date_today": datetime.now().strftime('%B %d, %Y')
        }
        
        # 5. Generate and Email PDF
        pdf = generate_pdf_blob('maintenance/invoice_template.html', context)
        
        # SAFETY CHECK: Only send if email exists
        if invoice_data.get('recipient_email'):
            send_email_with_pdf(
                invoice_data['recipient_email'], # FIXED: Use recipient_email
                invoice_data['recipient_name'],  # FIXED: Use recipient_name
                pdf, 
                f"Receipt_{bill_id}.pdf", 
                invoice_data
            )

        # 6. Notify the Treasurer
        treasurer = TreasurerRepository.get_treasurer_by_society(invoice_data['society_id'])
        if treasurer:
            NotificationRepository.create(
                user_id=treasurer['id'],
                title="Payment Received 💰",
                message=f"Flat {invoice_data['flat_number']} ({invoice_data['recipient_name']}) paid via Razorpay.",
                notif_type="finance"
            )

        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"VERIFY PAYMENT ERROR: {str(e)}") # LOG the error to terminal
        return jsonify({"status": "error", "message": str(e)}), 400

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

import secrets
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required

# Repositories & Services
from maintenance.repository import MaintenanceRepository
from notifications.repository import NotificationRepository
from treasurers.repository import TreasurerRepository
from utils.mail import send_email_with_pdf # Ensure this matches your mail file name
from utils.pdf_helper import generate_pdf_blob # Ensure this matches your PDF util


@owners_bp.route("/pay-simulation/<int:maintenance_id>", methods=["POST"])
@login_required
@role_required("owner", "tenant")
def pay_bill(maintenance_id):
    """
    Consolidated Payment Flow:
    1. Mark bill as Paid in DB.
    2. Notify Resident (Success).
    3. Notify Society Treasurer (New Collection).
    4. Generate & Email PDF Receipt.
    
    FIXED: Now handles both Owner and Tenant emails correctly.
    """
    try:
        # Step 1: Update Database with dummy transaction ID
        dummy_p_id = f"PAY_{secrets.token_hex(4).upper()}"
        MaintenanceRepository.mark_as_paid(
            maintenance_id, 
            method='Online Transfer', 
            p_id=dummy_p_id
        )

        # Step 2: Fetch all data needed (Includes COALESCE logic for Owner/Tenant)
        invoice_data = MaintenanceRepository.get_full_invoice_data(maintenance_id)

        # CRITICAL FIX: Stop if no email is found to prevent 'NoneType' crash
        if not invoice_data or not invoice_data.get('recipient_email'):
            flash("Payment recorded, but system could not find an email address to send the receipt.", "warning")
            return redirect(url_for("owners.my_maintenance"))

        # --- STEP 3: NOTIFICATION SYSTEM ---
        
        # A. Notify the RESIDENT (The person who just paid - Owner or Tenant)
        NotificationRepository.create(
            user_id=session["user"]["id"],
            title="Payment Successful ✅",
            message=f"Maintenance for {invoice_data['month']} {invoice_data['year']} is cleared. Receipt generated.",
            notif_type="payment"
        )

        # B. Notify the TREASURER
        treasurer = TreasurerRepository.get_treasurer_by_society(invoice_data['society_id'])
        
        if treasurer:
            payment_date = datetime.now().strftime("%d-%m-%Y")
            NotificationRepository.create(
                user_id=treasurer['id'],
                title="Payment Received 💰",
                message=f"Flat {invoice_data['flat_number']} ({invoice_data['recipient_name']}) paid ₹{invoice_data['amount']} on {payment_date}.",
                notif_type="finance"
            )

        # --- STEP 4: PDF & EMAIL RECEIPT ---

        # Prepare context using the unified recipient keys
        context = {
            "society": {
                "name": invoice_data['society_name'], 
                "address": invoice_data['society_address']
            },
            "user": {
                "full_name": invoice_data['recipient_name'], 
                "email": invoice_data['recipient_email']
            },
            "flat": {
                "flat_number": invoice_data['flat_number'], 
                "block_name": invoice_data['block_name']
            },
            "maintenance": invoice_data,
            "date_today": datetime.now().strftime('%B %d, %Y')
        }

        # Generate the PDF blob
        pdf_blob = generate_pdf_blob('maintenance/invoice_template.html', context)

        if pdf_blob:
            filename = f"Receipt_{invoice_data['flat_number']}_{invoice_data['month']}.pdf"
            
            # Send Email with PDF attachment (Using recipient keys)
            send_email_with_pdf(
                recipient_email=invoice_data['recipient_email'],
                recipient_name=invoice_data['recipient_name'],
                pdf_data=pdf_blob,
                filename=filename,
                maintenance=invoice_data
            )
            flash(f"Payment successful! Professional receipt has been emailed to {invoice_data['recipient_email']}. ✅", "success")
        else:
            flash("Payment recorded successfully, but receipt email generation failed.", "warning")

    except Exception as e:
        print(f"CRITICAL PAYMENT FLOW ERROR: {e}")
        flash(f"System Error during payment: {str(e)}", "danger")

    return redirect(url_for("owners.my_maintenance"))