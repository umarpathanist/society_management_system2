from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.repository import UserRepository
from auth.service import AuthService
from werkzeug.security import generate_password_hash, check_password_hash
from utils.decorators import login_required

auth_bp = Blueprint("auth", __name__)

def redirect_user_by_role(role):
    """
    Centralized helper function to handle landing pages for all roles.
    This fixes the 403 error by ensuring Treasurers go to the Dashboard.
    """
    if not role:
        return redirect(url_for("auth.login"))
    
    role = role.lower()
    
    # 1. Management Roles (Super Admin, Admin, Treasurer) -> Dashboard
    if role in ["super_admin", "admin", "treasurer"]:
        return redirect(url_for("dashboard.index"))
    
    # 2. Resident Roles (Owner, Tenant) -> My Flat Page
    elif role in ["owner", "tenant"]:
        return redirect(url_for("owners.my_flat"))
    
    # 3. Default Fallback
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect them to their dashboard/flat immediately
    if "user" in session:
        return redirect_user_by_role(session["user"].get("role"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Use the Service to handle authentication logic
        user, error = AuthService.authenticate(email, password)
        
        if error or not user:
            flash(error or "Invalid email or password", "danger")
            return redirect(url_for("auth.login"))

        # 1. Clear session to prevent session fixation attacks
        session.clear()

        # 2. Determine display name and standardized role
        display_name = user.get("full_name") or user.get("name") or "User"
        user_role = user.get("role").lower() if user.get("role") else "user"

        # 3. Store essential user data in the session
        session["user"] = {
            "id": user.get("id"),
            "full_name": display_name,
            "email": user.get("email"),
            "role": user_role,
            "society_id": user.get("society_id")
        }
        
        # Helper for quick access to society context across the app
        session["society_id"] = user.get("society_id")

        flash(f"Welcome back, {display_name}!", "success")
        
        # 4. Redirect based on user role using the unified helper
        return redirect_user_by_role(user_role)

    return render_template("auth/login.html")


# ---------------------------------------------------------
# NEW: CHANGE PASSWORD (FIXES BuildError)
# ---------------------------------------------------------
@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        user_id = session["user"]["id"]
        old_pwd = request.form.get("old_password")
        new_pwd = request.form.get("new_password")
        confirm_pwd = request.form.get("confirm_password")

        # 1. Fetch current user data
        user_data = UserRepository.get_by_id(user_id)

        # 2. Validation
        if not check_password_hash(user_data['password_hash'], old_pwd):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("auth.change_password"))

        if new_pwd != confirm_pwd:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("auth.change_password"))

        # 3. Update in DB
        hashed = generate_password_hash(new_pwd)
        UserRepository.update_password(user_id, hashed)
        
        flash("Password updated successfully! ✅", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/change_password.html")




import secrets # For generating random passwords
import string

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        # 1. Generate a random temporary password
        chars = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(chars) for i in range(8))
        
        # 2. Hash and update in DB
        hashed = generate_password_hash(temp_password)
        success = UserRepository.update_password_by_email(email, hashed)
        
        if success:
            # 3. Send email
            from utils.mail import send_password_reset
            send_password_reset(email, temp_password)
            flash("A new temporary password has been sent to your email! 📧", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Email address not found in our records.", "danger")

    return render_template("auth/forgot_password.html")



@auth_bp.route("/logout")
def logout():
    """
    Logs out the user and clears all session data.
    """
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))