import secrets
import razorpay
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, jsonify, current_app
)

from utils.decorators import login_required, role_required
from owners.service import OwnerService
from owners.repository import OwnerRepository
from maintenance.repository import MaintenanceRepository
from treasurers.repository import TreasurerRepository
from notifications.repository import NotificationRepository
from utils.pdf_helper import generate_pdf_blob
from utils.mail import send_email_with_pdf


owners_bp = Blueprint("owners", __name__, url_prefix="/owners")


# ---------------------------------------------------------
# 1. ADMIN: LIST OWNERS & TENANTS
# ---------------------------------------------------------
@owners_bp.route("/list")
@login_required
@role_required("admin", "super_admin")
def list_owners():
    user = session.get("user")
    user_role = user.get("role").lower()
    society_id = session.get("society_id")
    target_soc = None if user_role == "super_admin" else society_id
    users_list = OwnerRepository.get_users_by_society_and_roles(target_soc, ("owner", "tenant"))
    return render_template("owners/list.html", users=users_list)


# ---------------------------------------------------------
# 2. RESIDENT: DASHBOARD & DUES
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
# 3. RAZORPAY PAYMENT: CREATE ORDER & VERIFY
# ---------------------------------------------------------
@owners_bp.route("/create-payment-order/<int:bill_id>", methods=["POST"])
@login_required
def create_payment_order(bill_id):
    bill = MaintenanceRepository.get_full_invoice_data(bill_id)
    if not bill:
        return jsonify({"status": "error", "message": "Bill not found"}), 404

    try:
        client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'],
            current_app.config['RAZORPAY_KEY_SECRET']
        ))
        amount_paise = int(float(bill['amount']) * 100)
        order = client.order.create(data={
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"bill_{bill_id}"
        })
        MaintenanceRepository.save_order_id(bill_id, order['id'])
        return jsonify({
            "status": "success",
            "order_id": order['id'],
            "amount": order['amount'],
            "key": current_app.config['RAZORPAY_KEY_ID'],
            "full_name": bill['recipient_name'],
            "email": bill['recipient_email']
        })
    except Exception as e:
        print(f"ORDER CREATION ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@owners_bp.route("/verify-payment", methods=["POST"])
@login_required
def verify_payment():
    # ✅ FIXED: Handle missing or empty JSON body
    data = request.get_json(silent=True)

    if not data:
        print("VERIFY PAYMENT ERROR: No JSON data received")
        return jsonify({"status": "error", "message": "No payment data received"}), 400

    # ✅ FIXED: Validate required fields before processing
    required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'bill_id']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        print(f"VERIFY PAYMENT ERROR: Missing fields: {missing}")
        return jsonify({"status": "error", "message": f"Missing fields: {missing}"}), 400

    try:
        client = razorpay.Client(auth=(
            current_app.config['RAZORPAY_KEY_ID'],
            current_app.config['RAZORPAY_KEY_SECRET']
        ))

        # 1. Verify Razorpay signature
        client.utility.verify_payment_signature({
            'razorpay_order_id':   data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature':  data['razorpay_signature']
        })

        bill_id = data['bill_id']

        # 2. Mark bill as paid in DB
        MaintenanceRepository.mark_as_paid(
            bill_id,
            method='Razorpay Online',
            p_id=data['razorpay_payment_id']
        )

        # 3. Fetch full invoice data
        invoice_data = MaintenanceRepository.get_full_invoice_data(bill_id)

        # 4. Build PDF context
        context = {
            "society": {
                "name":    invoice_data['society_name'],
                "address": invoice_data['society_address']
            },
            "user": {
                "full_name": invoice_data['recipient_name'],
                "email":     invoice_data['recipient_email']
            },
            "flat": {
                "flat_number": invoice_data['flat_number'],
                "block_name":  invoice_data['block_name']
            },
            "maintenance": invoice_data,
            "date_today": datetime.now().strftime('%B %d, %Y')
        }

        # 5. Generate and email PDF receipt
        pdf = generate_pdf_blob('maintenance/invoice_template.html', context)
        if invoice_data.get('recipient_email'):
            send_email_with_pdf(
                invoice_data['recipient_email'],
                invoice_data['recipient_name'],
                pdf,
                f"Receipt_{bill_id}.pdf",
                invoice_data
            )

        # 6. Notify the treasurer
        treasurer = TreasurerRepository.get_treasurer_by_society(invoice_data['society_id'])
        if treasurer:
            NotificationRepository.create(
                user_id   = treasurer['id'],
                title     = "Payment Received 💰",
                message   = f"Flat {invoice_data['flat_number']} ({invoice_data['recipient_name']}) paid via Razorpay.",
                notif_type= "finance"
            )

        return jsonify({"status": "success"})

    except Exception as e:
        print(f"VERIFY PAYMENT ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400


# ---------------------------------------------------------
# 4. SIMULATION PAYMENT (For Testing Without Razorpay)
# ---------------------------------------------------------
@owners_bp.route("/pay-simulation/<int:maintenance_id>", methods=["POST"])
@login_required
@role_required("owner", "tenant")
def pay_bill(maintenance_id):
    try:
        # 1. Mark as paid with dummy transaction ID
        dummy_p_id = f"PAY_{secrets.token_hex(4).upper()}"
        MaintenanceRepository.mark_as_paid(
            maintenance_id,
            method='Online Transfer',
            p_id=dummy_p_id
        )

        # 2. Fetch full invoice data
        invoice_data = MaintenanceRepository.get_full_invoice_data(maintenance_id)

        if not invoice_data or not invoice_data.get('recipient_email'):
            flash("Payment recorded, but no email address found to send receipt.", "warning")
            return redirect(url_for("owners.my_maintenance"))

        # 3a. Notify the resident
        NotificationRepository.create(
            user_id   = session["user"]["id"],
            title     = "Payment Successful ✅",
            message   = f"Maintenance for {invoice_data['month']} {invoice_data['year']} is cleared. Receipt generated.",
            notif_type= "payment"
        )

        # 3b. Notify the treasurer
        treasurer = TreasurerRepository.get_treasurer_by_society(invoice_data['society_id'])
        if treasurer:
            payment_date = datetime.now().strftime("%d-%m-%Y")
            NotificationRepository.create(
                user_id   = treasurer['id'],
                title     = "Payment Received 💰",
                message   = f"Flat {invoice_data['flat_number']} ({invoice_data['recipient_name']}) paid ₹{invoice_data['amount']} on {payment_date}.",
                notif_type= "finance"
            )

        # 4. Generate and email PDF receipt
        context = {
            "society": {
                "name":    invoice_data['society_name'],
                "address": invoice_data['society_address']
            },
            "user": {
                "full_name": invoice_data['recipient_name'],
                "email":     invoice_data['recipient_email']
            },
            "flat": {
                "flat_number": invoice_data['flat_number'],
                "block_name":  invoice_data['block_name']
            },
            "maintenance": invoice_data,
            "date_today": datetime.now().strftime('%B %d, %Y')
        }

        pdf_blob = generate_pdf_blob('maintenance/invoice_template.html', context)
        if pdf_blob:
            filename = f"Receipt_{invoice_data['flat_number']}_{invoice_data['month']}.pdf"
            send_email_with_pdf(
                recipient_email = invoice_data['recipient_email'],
                recipient_name  = invoice_data['recipient_name'],
                pdf_data        = pdf_blob,
                filename        = filename,
                maintenance     = invoice_data
            )
            flash(f"Payment successful! Receipt emailed to {invoice_data['recipient_email']}. ✅", "success")
        else:
            flash("Payment recorded, but receipt email generation failed.", "warning")

    except Exception as e:
        print(f"CRITICAL PAYMENT FLOW ERROR: {e}")
        flash(f"System Error during payment: {str(e)}", "danger")

    return redirect(url_for("owners.my_maintenance"))


# ---------------------------------------------------------
# 5. CRUD: ADD, EDIT, DELETE OWNERS
# ---------------------------------------------------------
@owners_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def add_owner():
    if request.method == "POST":
        try:
            OwnerService.create_owner_or_tenant({
                "full_name":  request.form.get("full_name"),
                "email":      request.form.get("email"),
                "role":       request.form.get("role"),
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
                "email":     request.form.get("email"),
                "role":      request.form.get("role")
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