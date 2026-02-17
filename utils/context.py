from flask import session, request
from admin.service import AdminService
from blocks.service import BlockService


def _get_user_from_session():
    """
    Build user dict from session primitives
    """
    if "user_id" not in session:
        return None

    return {
        "id": session.get("user_id"),
        "email": session.get("email"),
        "role": session.get("role"),
        "society_id": session.get("society_id"),
    }


def load_sidebar_blocks():
    user = _get_user_from_session()

    if not user:
        return {}

    # Sidebar only for flats pages
    if not request.endpoint or not request.endpoint.startswith("flats."):
        return {"sidebar_blocks": []}

    # SUPER admin → no sidebar blocks
    if user["role"] == "super_admin":
        return {"sidebar_blocks": []}

    society_ids = AdminService.get_assigned_society_ids(user["id"])
    if not society_ids:
        return {"sidebar_blocks": []}

    blocks = BlockService.get_by_society_ids(society_ids)

    return {"sidebar_blocks": blocks}


def inject_current_user():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "email": session.get("email"),
            "role": session.get("role"),
            "society_id": session.get("society_id"),
            "is_authenticated": bool(session.get("user_id")),
        }
    }


import random
import string

def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
