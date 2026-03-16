from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required, role_required
from tickets.repository import TicketRepository
from auth.repository import UserRepository
from notifications.repository import NotificationRepository

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")

@tickets_bp.route("/")
@login_required
def list_tickets():
    user = session["user"]
    role = user.get("role").lower()
    society_id = session.get("society_id")

    if role in ['admin', 'treasurer'] and society_id:
        tickets = TicketRepository.get_by_society(society_id)
    else:
        tickets = TicketRepository.get_by_user(user['id'])
    return render_template("tickets/list.html", tickets=tickets)

# tickets/routes.py

@tickets_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_ticket():
    user = session.get("user")
    
    if request.method == "POST":
        # 1. Get society_id from session or database
        society_id = session.get("society_id")
        
        if not society_id:
            from auth.repository import UserRepository
            user_db = UserRepository.get_by_id(user['id'])
            if user_db:
                # Standardizing key access
                society_id = user_db.get('society_id')

        # DEBUG: Check your VS Code terminal for this message!
        print(f"DEBUG: Attempting ticket for User {user['id']} in Society {society_id}")

        if not society_id:
            flash("Error: Your profile is not linked to a society. Please contact Admin.", "danger")
            return redirect(url_for("tickets.list_tickets"))

        try:
            # 2. Save to Repository
            TicketRepository.create({
                "user_id": user["id"],
                "society_id": society_id,
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "category": request.form.get("category"),
                "priority": request.form.get("priority")
            })
            flash("Request submitted successfully! 🛠️", "success")
            return redirect(url_for("tickets.list_tickets"))
            
        except Exception as e:
            # Flashes the actual system error message
            flash(f"Submission Error: {str(e)}", "danger")

    return render_template("tickets/add.html")

@tickets_bp.route("/view/<int:id>")
@login_required
def view_ticket(id):
    ticket = TicketRepository.get_by_id(id)
    if not ticket:
        flash("Ticket not found.", "danger")
        return redirect(url_for("tickets.list_tickets"))

    comments = TicketRepository.get_comments(id)
    return render_template("tickets/view.html", ticket=ticket, comments=comments)

@tickets_bp.route("/comment/<int:ticket_id>", methods=["POST"])
@login_required
def add_comment(ticket_id):
    comment_text = request.form.get("comment")
    user = session["user"]
    if comment_text:
        TicketRepository.add_comment(ticket_id, user["id"], comment_text)
        
        # Trigger Notification if Admin comments
        if user['role'] in ['admin', 'super_admin']:
            ticket = TicketRepository.get_by_id(ticket_id)
            NotificationRepository.create(
                user_id=ticket['user_id'],
                title=f"Update on Ticket #{ticket_id}",
                message=f"Admin: {comment_text[:50]}...",
                notif_type="system"
            )
        flash("Update posted.", "success")
    return redirect(url_for("tickets.view_ticket", id=ticket_id))

@tickets_bp.route("/status/<int:ticket_id>", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def update_status(ticket_id):
    new_status = request.form.get("status")
    TicketRepository.update_status(ticket_id, new_status)
    
    ticket = TicketRepository.get_by_id(ticket_id)
    NotificationRepository.create(
        user_id=ticket['user_id'],
        title="Ticket Status Updated",
        message=f"Ticket #TKT-{ticket_id} is now '{new_status.replace('_', ' ').title()}'.",
        notif_type="system"
    )
    flash(f"Status changed to {new_status}.", "success")
    return redirect(url_for("tickets.view_ticket", id=ticket_id))


# Inside tickets/routes.py

@tickets_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin", "super_admin") # Strictly restrict access
def delete_ticket(id):
    try:
        TicketRepository.delete(id)
        flash(f"Ticket #TKT-{id} has been permanently deleted.", "success")
    except Exception as e:
        flash(f"Error deleting ticket: {str(e)}", "danger")
        
    return redirect(url_for("tickets.list_tickets"))
