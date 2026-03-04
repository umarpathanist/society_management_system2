from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required
from notifications.repository import NotificationRepository

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")



@notifications_bp.route("/")
@login_required
def index():
    user_id = session["user"]["id"]
    notifs = NotificationRepository.get_all_by_user(user_id)
    
    count = sum(1 for n in notifs if not n['is_read'])
    
    return render_template("notifications/index.html", 
                           notifications=notifs, 
                           unread_notif_count=count) 

@notifications_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    NotificationRepository.delete(id, session["user"]["id"])
    flash("Notification removed.", "info")
    return redirect(url_for("notifications.index"))

@notifications_bp.route("/clear-all", methods=["POST"])
@login_required
def clear_all():
    NotificationRepository.delete_all(session["user"]["id"])
    flash("Inbox cleared! ✨", "success")
    return redirect(url_for("notifications.index"))

@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def read_all():
    NotificationRepository.mark_all_read(session["user"]["id"])
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications.index"))

@notifications_bp.route("/bulk-delete", methods=["POST"])
@login_required
def bulk_delete():
    ids = request.form.getlist("notif_ids")
    if not ids:
        flash("No items selected.", "warning")
        return redirect(url_for("notifications.index"))
        
    for notif_id in ids:
        NotificationRepository.delete(notif_id, session["user"]["id"])
    
    flash(f"Removed {len(ids)} notifications.", "info")
    return redirect(url_for("notifications.index"))