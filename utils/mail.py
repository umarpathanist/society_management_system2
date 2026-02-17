# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import os

# def send_email(to_email, subject, html_content):
#     msg = MIMEMultipart()
#     msg["From"] = os.getenv("MAIL_DEFAULT_SENDER")
#     msg["To"] = to_email
#     msg["Subject"] = subject

#     msg.attach(MIMEText(html_content, "html"))

#     server = smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT")))
#     server.starttls()
#     server.login(
#         os.getenv("MAIL_USERNAME"),
#         os.getenv("MAIL_PASSWORD")
#     )
#     server.send_message(msg)
#     server.quit()



from flask_mail import Message
from extensions import mail
from flask import current_app
import threading

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print("Login details email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")



def send_login_details(recipient_email, recipient_name, password, role):
    # Get the real app object to pass into the background thread
    app = current_app._get_current_object()
    
    subject = f"Welcome to Society Management - Your {role.title()} Account"
    
    body = f"""
    Hello {recipient_name},

    Your account has been successfully created in the Society Management System.
    
    Access Details:
    --------------------------------------
    Login URL: http://127.0.0.1:5000/login
    Email: {recipient_email}
    Password: {password}
    Role: {role.title()}
    --------------------------------------
    
    Note: Please change your password after your first login for security.
    
    Regards,
    Society Management Admin
    """
    
    msg = Message(subject, recipients=[recipient_email], body=body)
    
    # Run in background thread so the user doesn't wait
    threading.Thread(target=send_async_email, args=(app, msg)).start()



def send_maintenance_reminder(recipient_email, recipient_name, amount, month, year):
    """Sends a notification for new or pending maintenance."""
    app = current_app._get_current_object()
    subject = f"🚨 Maintenance Bill Generated: {month} {year}"
    
    body = f"""
    Hello {recipient_name},

    Your maintenance bill for {month} {year} has been generated.
    
    Amount: ₹{amount}
    Status: Unpaid
    
    Please log in to the portal to clear your dues.
    Login URL: http://127.0.0.1:5000/login

    Regards,
    Society Management Admin
    """
    
    msg = Message(subject, recipients=[recipient_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()
    

# utils/mail.py

def send_password_reset(recipient_email, new_password):
    app = current_app._get_current_object()
    subject = "🔑 Password Reset - Society Management"
    
    body = f"""
    Hello,

    Your password has been reset by the system.
    
    New Login Details:
    --------------------------
    Email: {recipient_email}
    Temporary Password: {new_password}
    --------------------------
    
    Please log in and change your password immediately for security.
    URL: http://127.0.0.1:5000/login

    Regards,
    Society HQ Support
    """
    
    msg = Message(subject, recipients=[recipient_email], body=body)
    threading.Thread(target=send_async_email, args=(app, msg)).start()