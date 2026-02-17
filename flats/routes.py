# from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session, jsonify
# from flats.repository import FlatRepository
# from utils.decorators import login_required, role_required
# from blocks.service import BlockService
# from flats.service import FlatService
# from admin.service import AdminService
# from auth.repository import UserRepository

# flats_bp = Blueprint("flats", __name__, url_prefix="/flats")



# from flask import Blueprint, render_template, abort, session
# from utils.decorators import login_required
# from flats.repository import FlatRepository
# from blocks.repository import BlockRepository

# flats_bp = Blueprint("flats", __name__, url_prefix="/flats")

# # flats/routes.py
# from flats.repository import FlatRepository
# from blocks.repository import BlockRepository
# from owners.repository import OwnerRepository # Ensure this is imported

# @flats_bp.route("/<int:block_id>")
# @login_required
# def list_flats(block_id):
#     # 1. Fetch block info to get the society_id
#     block = BlockRepository.get_by_id(block_id)
#     if not block:
#         abort(404)
        
#     # 2. Fetch all flats for this block
#     flats_list = FlatRepository.get_by_block(block_id)

#     # 3. Fetch all owners and tenants for the dropdown (FIXED LOGIC)
#     # We use the method we created earlier in OwnerRepository
#     owners = OwnerRepository.get_users_by_society_and_roles(block['society_id'], ('owner',))
#     tenants = OwnerRepository.get_users_by_society_and_roles(block['society_id'], ('tenant',))

#     # 4. Fetch all blocks in society for the block-switcher dropdown
#     all_blocks = BlockRepository.get_by_society(block['society_id'])

#     return render_template(
#         "flats/list.html", 
#         block=block, 
#         flats=flats_list,
#         all_blocks=all_blocks,
#         owners=owners,   # Passing the list to HTML
#         tenants=tenants  # Passing the list to HTML
#     )




# @flats_bp.route("/add/<int:block_id>", methods=["GET", "POST"])
# @login_required
# @role_required("admin")
# def add_flat(block_id):
#     block = BlockService.get_by_id(block_id)
#     if not block:
#         abort(404)

#     if request.method == "POST":
#         flat_number = request.form.get("flat_number")
#         floor_number = request.form.get("floor_number", 1)

#         if not flat_number:
#             flash("Flat number is required", "danger")
#             return redirect(request.referrer)

#         FlatService.create({
#             "block_id": block_id,
#             "flat_number": flat_number,
#             "floor_number": floor_number
#         })

#         flash("Flat added successfully", "success")
#         return redirect(url_for("flats.list_flats", block_id=block_id))

#     return render_template("flats/add.html", block=block)

# @flats_bp.route("/<int:flat_id>/assign", methods=["POST"])
# @login_required
# @role_required("admin")
# def assign_flat(flat_id):
#     user_id = request.form.get("user_id")
#     user_role = request.form.get("role")  # Should be 'owner' or 'tenant'

#     if not user_id or user_role not in ("owner", "tenant"):
#         flash("Please select a valid user and role", "danger")
#         return redirect(request.referrer)

#     try:
#         FlatService.assign_flat_to_user(
#             flat_id=flat_id,
#             user_id=int(user_id),
#             user_role=user_role
#         )
#         flash(f"{user_role.capitalize()} assigned successfully", "success")
#     except Exception as e:
#         flash(f"Error: {str(e)}", "danger")

#     flat = FlatService.get_by_id(flat_id)
#     return redirect(url_for("flats.list_flats", block_id=flat["block_id"]))

# @flats_bp.route("/<int:flat_id>/toggle", methods=["POST"])
# @login_required
# def toggle_flat(flat_id):
#     user = session.get("user")
#     flat = FlatService.get_by_id(flat_id)
#     if not flat:
#         abort(404)

#     # Permission check
#     if user["role"] != "super_admin":
#         if not AdminService.can_manage_flats(user["id"], flat["society_id"]):
#             return jsonify({"error": "Unauthorized"}), 403

#     FlatService.toggle_status(flat_id)
#     return jsonify({"success": True})

# @flats_bp.route("/unassign/<int:flat_id>/<role>", methods=["POST"])
# @login_required
# @role_required("admin")
# def unassign(flat_id, role):
#     if role not in ("owner", "tenant"):
#         flash("Invalid role", "danger")
#         return redirect(request.referrer)

#     FlatRepository.unassign_user(flat_id, role)
#     flash(f"{role.capitalize()} removed successfully from the flat.", "success")
#     return redirect(request.referrer)






from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from utils.decorators import login_required, role_required

# Repositories
from flats.repository import FlatRepository
from blocks.repository import BlockRepository
from owners.repository import OwnerRepository

flats_bp = Blueprint("flats", __name__, url_prefix="/flats")

# ---------------------------------------------------------
# 1. LIST FLATS (URL: /flats/<block_id>)
# ---------------------------------------------------------
@flats_bp.route("/<int:block_id>")
@login_required
def list_flats(block_id):
    """Fetches and displays all flats for a specific block."""
    block = BlockRepository.get_by_id(block_id)
    if not block: 
        abort(404)

    flats_list = FlatRepository.get_by_block(block_id)
    
    # Data for the assignment dropdowns and block switcher
    society_id = block['society_id']
    owners = OwnerRepository.get_users_by_society_and_roles(society_id, ('owner',))
    tenants = OwnerRepository.get_users_by_society_and_roles(society_id, ('tenant',))
    all_blocks = BlockRepository.get_by_society(society_id)

    return render_template("flats/list.html", 
                           block=block, 
                           flats=flats_list,
                           owners=owners,
                           tenants=tenants,
                           all_blocks=all_blocks)


# ---------------------------------------------------------
# 2. ADD SINGLE FLAT (URL: /flats/add/<block_id>) - FIXES BuildError
# ---------------------------------------------------------
@flats_bp.route("/add/<int:block_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_flat(block_id):
    """
    FIXES BuildError: could not build url for endpoint 'flats.add_flat'
    Allows manual addition of a single flat to a block.
    """
    block = BlockRepository.get_by_id(block_id)
    if not block:
        abort(404)

    if request.method == "POST":
        flat_number = request.form.get("flat_number")
        floor_number = request.form.get("floor_number", 1)

        if not flat_number:
            flash("Flat number is required", "danger")
            return redirect(url_for("flats.add_flat", block_id=block_id))

        try:
            # Create a simple list to reuse our create_multiple logic
            FlatRepository.create_multiple([{
                "block_id": block_id,
                "flat_number": flat_number,
                "floor_number": floor_number
            }])
            flash(f"Flat {flat_number} added successfully! ✅", "success")
            return redirect(url_for("flats.list_flats", block_id=block_id))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("flats/add.html", block=block)


# ---------------------------------------------------------
# 3. PERFORM ASSIGNMENT (URL: /flats/assign/<flat_id>)
# ---------------------------------------------------------
@flats_bp.route("/assign/<int:flat_id>", methods=["POST"])
@login_required
@role_required("admin")
def assign_flat(flat_id):
    flat = FlatRepository.get_by_id(flat_id)
    if not flat:
        flash("Flat not found.", "danger")
        return redirect(request.referrer)

    user_id = request.form.get("user_id")
    role = request.form.get("role") 

    if not user_id or not role:
        flash("Please select both a person and a role.", "warning")
        return redirect(request.referrer)

    try:
        FlatRepository.assign_user(flat_id, user_id, role)
        flash("Flat assigned successfully! ✅", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for("flats.list_flats", block_id=flat['block_id']))


# ---------------------------------------------------------
# 4. UNASSIGN USER (POST)
# ---------------------------------------------------------
@flats_bp.route("/unassign/<int:flat_id>/<role>", methods=["POST"])
@login_required
@role_required("admin")
def unassign(flat_id, role):
    try:
        FlatRepository.unassign_user(flat_id, role)
        flash(f"{role.capitalize()} removed successfully.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for(request.referrer))