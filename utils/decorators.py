from functools import wraps
from flask import session, redirect, url_for, abort, request 

from admin.service import AdminService
from blocks.repository import BlockRepository


# ======================================================
# SESSION USER HELPER
# ======================================================
def _get_user_from_session():
    if "user_id" not in session:
        return None

    return {
        "id": session.get("user_id"),
        "email": session.get("email"),
        "role": session.get("role"),
        "society_id": session.get("society_id"),
    }


# ======================================================
# LOGIN REQUIRED
# ======================================================

from functools import wraps
from flask import session, redirect, url_for

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            print("LOGIN REQUIRED FAILED, SESSION:", dict(session))
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper




# ======================================================
# ROLE REQUIRED
# ======================================================
from functools import wraps
from flask import session, abort

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = session.get("user")

            if not user:
                return redirect(url_for("auth.login"))

            if user.get("role") not in roles:
                abort(403)

            return view_func(*args, **kwargs)
        return wrapper
    return decorator

# ======================================================
# SOCIETY ACCESS REQUIRED
# ======================================================
def society_access_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        role = session.get("role")

        if not user_id:
            return redirect(url_for("auth.login"))

        # ✅ super_admin → full access
        if role == "super_admin":
            return view_func(*args, **kwargs)

        # ❌ ADMIN / others → blocked for now
        abort(403)

    return wrapper


# ======================================================
# PERMISSION REQUIRED  ✅ THIS IS WHAT WAS MISSING
# ======================================================
def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                abort(401)

            user_id = session.get("user_id")

            from permissions.service import PermissionService

            if not PermissionService.user_has_permission(
                user_id=user_id,
                permission_code=permission_code
            ):
                abort(403)

            return view_func(*args, **kwargs)

        return wrapper
    return decorator


from functools import wraps
from flask import abort, session


def role_required(*allowed_roles):
    """
    Restricts access based on user role stored in session.
    Expected session structure:
    session["user"]["role"]
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")

            if not user:
                abort(401)  # Not logged in

            user_role = user.get("role")

            if user_role not in allowed_roles:
                abort(403)  # Forbidden

            return view(*args, **kwargs)

        return wrapped
    return decorator


from functools import wraps
from flask import session, redirect, url_for, flash, abort


# ======================================================
# LOGIN REQUIRED
# ======================================================
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login to continue", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


# ======================================================
# ROLE REQUIRED
# Usage: @role_required("admin", "super_admin")
# ======================================================
def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user = session.get("user")

            if not user:
                flash("Please login to continue", "danger")
                return redirect(url_for("auth.login"))

            if user.get("role") not in allowed_roles:
                abort(403)

            return view_func(*args, **kwargs)
        return wrapped
    return decorator
