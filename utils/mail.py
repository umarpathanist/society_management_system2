from flask_mail import Message
from extensions import mail
from flask import current_app, render_template
import threading

# ✅ Live server URL
BASE_URL = "https://society.fairhospitality.in"

# ---------------------------------------------------------
# CORE: Async email sender
# ---------------------------------------------------------
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Email sent to: {msg.recipients[0]}")
        except Exception as e:
            print(f"Mail Delivery Failed: {e}")


# ---------------------------------------------------------
# 1. Send Login Details (Welcome Email)
# ---------------------------------------------------------
def send_login_details(recipient_email, recipient_name, password, role):
    app = current_app._get_current_object()
    subject = f"Welcome to SocietyHQ - Your {role.title()} Account"
    body = f"""
Hello {recipient_name},

Your account has been successfully created in SocietyHQ.

Access Details:
--------------------------------------
Login URL : {BASE_URL}/login
Email     : {recipient_email}
Password  : {password}
Role      : {role.title()}
--------------------------------------

Please change your password after your first login for security.

Regards,
SocietyHQ Admin
    """
    msg = Message(subject, recipients=[recipient_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()


# ---------------------------------------------------------
# 2. Maintenance Bill Reminder
# ---------------------------------------------------------
def send_maintenance_reminder(recipient_email, recipient_name, amount, month, year):
    app = current_app._get_current_object()
    subject = f"🚨 Maintenance Bill Generated: {month} {year}"
    body = f"""
Hello {recipient_name},

Your maintenance bill for {month} {year} has been generated.

Amount : ₹{amount}
Status : Unpaid

Please log in to the portal to clear your dues:
{BASE_URL}/login

Regards,
SocietyHQ Admin
    """
    msg = Message(subject, recipients=[recipient_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()


# ---------------------------------------------------------
# 3. Password Reset
# ---------------------------------------------------------
def send_password_reset(recipient_email, new_password):
    app = current_app._get_current_object()
    subject = "🔑 Password Reset - SocietyHQ"
    body = f"""
Hello,

Your password has been reset by the system.

New Login Details:
--------------------------
Email             : {recipient_email}
Temporary Password: {new_password}
--------------------------

Please log in and change your password immediately:
{BASE_URL}/login

Regards,
SocietyHQ Support
    """
    msg = Message(subject, recipients=[recipient_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()


# ---------------------------------------------------------
# 4. Payment Receipt Email with PDF Attachment
# ---------------------------------------------------------
def send_email_with_pdf(recipient_email, recipient_name, pdf_data, filename, maintenance):
    app = current_app._get_current_object()
    subject = f"✅ Payment Received: {maintenance['month']} {maintenance['year']} - SocietyHQ"

    with app.app_context():
        html_body = render_template(
            'emails/payment_receipt.html',
            name=recipient_name,
            m=maintenance
        )

    msg = Message(subject, recipients=[recipient_email], html=html_body)

    if pdf_data:
        msg.attach(filename, "application/pdf", pdf_data)

    threading.Thread(target=send_async_email, args=(app, msg)).start()


# ---------------------------------------------------------
# 5. SLA Escalation Email
# ---------------------------------------------------------
def send_sla_escalation_email(admin_email, admin_name, ticket_id, ticket_title):
    app = current_app._get_current_object()
    subject = f"⚠️ SLA ESCALATION: Ticket #TKT-{ticket_id} is Overdue"
    body = f"""
Hello {admin_name},

SYSTEM ALERT: A maintenance request has exceeded the 48-hour SLA period.

Ticket Details:
--------------------------------------
Ticket ID : #TKT-{ticket_id}
Subject   : {ticket_title}
Status    : Open (Overdue)
--------------------------------------

Please review and resolve this request immediately:
{BASE_URL}/tickets/view/{ticket_id}

Regards,
SocietyHQ Automation Engine
    """
    msg = Message(subject, recipients=[admin_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()


# ---------------------------------------------------------
# 6. Payment Received - To Resident
# ---------------------------------------------------------
def send_payment_received_to_resident(recipient_email, recipient_name, amount, month, year, payment_method, flat_number):
    app = current_app._get_current_object()
    subject = f"✅ Payment Received: {month} {year} - SocietyHQ"
    body = f"""
Hello {recipient_name},

We have successfully received your maintenance payment.

Payment Details:
--------------------------------------
Flat Number  : {flat_number}
Month        : {month} {year}
Amount Paid  : ₹{float(amount):,.2f}
Payment Mode : {payment_method}
Status       : PAID ✅
--------------------------------------

Thank you for your timely payment.
View your payment history at: {BASE_URL}/login

Regards,
SocietyHQ Team
    """
    msg = Message(subject, recipients=[recipient_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()


# ---------------------------------------------------------
# 7. Payment Confirmation - To Treasurer
# ---------------------------------------------------------
def send_payment_confirmation_to_treasurer(treasurer_email, treasurer_name, resident_name, flat_number, amount, month, year, payment_method):
    app = current_app._get_current_object()
    subject = f"🧾 Payment Recorded: {flat_number} - {month} {year}"
    body = f"""
Hello {treasurer_name},

A maintenance payment has been successfully recorded.

Transaction Summary:
--------------------------------------
Resident     : {resident_name}
Flat Number  : {flat_number}
Month        : {month} {year}
Amount       : ₹{float(amount):,.2f}
Payment Mode : {payment_method}
Recorded By  : {treasurer_name}
Status       : PAID ✅
--------------------------------------

This is an automated confirmation. No action required.

Regards,
SocietyHQ System
    """
    msg = Message(subject, recipients=[treasurer_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()