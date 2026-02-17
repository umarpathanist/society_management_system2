# from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# from blocks.repository import BlockRepository
# from utils.decorators import login_required, role_required
# from blocks.service import BlockService
# from societies.service import SocietyService



# blocks_bp = Blueprint("blocks", __name__, url_prefix="/blocks")


# # ======================================================
# # LIST BLOCKS
# # ======================================================
# # @blocks_bp.route("/<int:society_id>", methods=["GET"])
# # @login_required
# # @role_required("super_admin", "admin")
# # def list_blocks(society_id):
# #     society = SocietyService.get_by_id(society_id)
# #     blocks = BlockService.get_by_society(society_id)

# #     return render_template(
# #         "blocks/list.html",
# #         society=society,
# #         blocks=blocks
# #     )

# @blocks_bp.route("/<int:society_id>")
# @login_required
# @role_required("super_admin", "admin")
# def list_blocks(society_id):
#     blocks = BlockService.get_by_society(society_id)

#     return render_template(
#         "blocks/list.html",
#         blocks=blocks,
#         society_id=society_id
#     )



# @blocks_bp.route("/add/<int:society_id>", methods=["GET", "POST"])
# @login_required
# @role_required("super_admin", "admin")
# def add_block(society_id):
#     if request.method == "POST":
#         BlockService.create({
#             "society_id": society_id,
#             "name": request.form.get("name"),
#             "floors": request.form.get("floors"),
#         })
#         return redirect(url_for("blocks.list_blocks", society_id=society_id))

#     return render_template("blocks/add.html", society_id=society_id)


# @blocks_bp.route("/edit/<int:id>", methods=["GET", "POST"])
# @login_required
# @role_required("admin", "super_admin")
# def edit_block(id):
#     block = BlockRepository.get_by_id(id)
#     if not block:
#         flash("Block not found", "danger")
#         return redirect(request.referrer)

#     if request.method == "POST":
#         name = request.form.get("name")
#         floors = request.form.get("floors")
#         try:
#             BlockRepository.update(id, name, floors)
#             flash("Block updated successfully!", "success")
#             return redirect(url_for('blocks.list_blocks', society_id=block['society_id']))
#         except Exception as e:
#             flash(f"Error: {str(e)}", "danger")

#     return render_template("blocks/edit.html", block=block)

# @blocks_bp.route("/delete/<int:id>", methods=["POST"])
# @login_required
# @role_required("admin", "super_admin")
# def delete_block(id):
#     block = BlockRepository.get_by_id(id)
#     if not block:
#         flash("Block not found", "danger")
#         return redirect(request.referrer)

#     try:
#         BlockRepository.delete(id)
#         flash("Block deleted successfully!", "success")
#     except Exception as e:
#         flash(f"Error: {str(e)}", "danger")
    
#     return redirect(url_for('blocks.list_blocks', society_id=block['society_id']))






from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required

# Repositories
from blocks.repository import BlockRepository
from societies.repository import SocietyRepository
from flats.repository import FlatRepository

blocks_bp = Blueprint("blocks", __name__, url_prefix="/blocks")

# ---------------------------------------------------------
# 1. LIST BLOCKS (URL: /blocks/<society_id>)
# ---------------------------------------------------------
@blocks_bp.route("/<int:society_id>")
@login_required
def list_blocks(society_id):
    blocks_list = BlockRepository.get_by_society(society_id)
    return render_template("blocks/list.html", blocks=blocks_list, society_id=society_id)


# ---------------------------------------------------------
# 2. ADD BLOCK (URL: /blocks/add/<society_id>)
# ---------------------------------------------------------
@blocks_bp.route("/add/<int:society_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def add_block(society_id):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        floors = int(request.form.get("floors") or 0)
        fpf = int(request.form.get("flats_per_floor") or 0)

        try:
            # Create Block
            block_id = BlockRepository.create(society_id, name, floors)
            
            if block_id:
                # Auto-generate flats
                label = name.split()[-1] if name else "B"
                new_flats = []
                for f in range(1, floors + 1):
                    for i in range(1, fpf + 1):
                        new_flats.append({
                            "block_id": block_id,
                            "flat_number": f"{label}-{f}{i:02d}",
                            "floor_number": f
                        })
                
                if new_flats:
                    FlatRepository.create_multiple(new_flats)
                    flash(f"Block '{name}' and its flats generated! ✅", "success")
                
                return redirect(url_for('blocks.list_blocks', society_id=society_id))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("blocks/add.html", society_id=society_id)


# ---------------------------------------------------------
# 3. EDIT BLOCK (URL: /blocks/edit/<id>)
# ---------------------------------------------------------
@blocks_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def edit_block(id):
    """FIXES BuildError: blocks.edit_block"""
    block = BlockRepository.get_by_id(id)
    if not block:
        flash("Block not found", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == "POST":
        new_name = request.form.get("name")
        new_floors = int(request.form.get("floors") or 0)
        try:
            BlockRepository.update(id, new_name, new_floors)
            flash("Block updated successfully! ✅", "success")
            return redirect(url_for('blocks.list_blocks', society_id=block['society_id']))
        except Exception as e:
            flash(f"Update Error: {str(e)}", "danger")

    return render_template("blocks/edit.html", block=block)


# ---------------------------------------------------------
# 4. DELETE BLOCK (URL: /blocks/delete/<id>)
# ---------------------------------------------------------
@blocks_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def delete_block(id):
    block = BlockRepository.get_by_id(id)
    if block:
        try:
            BlockRepository.delete(id)
            flash("Block deleted successfully.", "success")
            return redirect(url_for('blocks.list_blocks', society_id=block['society_id']))
        except Exception as e:
            flash(f"Delete Error: {str(e)}", "danger")
    return redirect(url_for('dashboard.index'))