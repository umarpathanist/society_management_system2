from flask import Blueprint, render_template
from maintenance.repository import MaintenanceRepository
from utils.decorators import login_required, role_required, permission_required


maintenance_bp = Blueprint(
    "maintenance",
    __name__,
    url_prefix="/maintenance"
)


# -------------------------------------------------
# MAINTENANCE DASHBOARD (admin / treasurer)
# -------------------------------------------------
@maintenance_bp.route("/")
@login_required
@permission_required("view_maintenance")
def maintenance_dashboard():
    return render_template("maintenance/dashboard.html")


from utils.pdf_helper import generate_pdf_blob # Import the helper we discussed
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from maintenance.repository import MaintenanceRepository # <--- ADD THIS



from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from maintenance.repository import MaintenanceRepository
from utils.pdf_helper import generate_pdf_blob
from datetime import datetime
from utils.decorators import login_required

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")

@maintenance_bp.route("/invoice/download/<int:m_id>")
@login_required
def download_invoice(m_id):
    # 1. Fetch the data using our special JOIN query
    invoice_data = MaintenanceRepository.get_full_invoice_data(m_id)
    
    if not invoice_data:
        flash("Invoice record not found.", "danger")
        return redirect(request.referrer or url_for('dashboard.index_redirect'))

    # 2. FIX: Structure the context so 'society', 'user', etc. are defined
    # This solves the 'society is undefined' error
    context = {
        "society": {
            "name": invoice_data['society_name'],
            "address": invoice_data['society_address']
        },
        "user": {
            "full_name": invoice_data['recipient_name'],
            "email": invoice_data['recipient_email']
        },
        "flat": {
            "flat_number": invoice_data['flat_number'],
            "block_name": invoice_data['block_name']
        },
        "maintenance": invoice_data, # Contains amount, month, year, id, status, etc.
        "date_today": datetime.now().strftime('%B %d, %Y')
    }

    # 3. Generate PDF
    try:
        pdf_file = generate_pdf_blob('maintenance/invoice_template.html', context)
        
        if not pdf_file:
            flash("Error rendering PDF document.", "danger")
            return redirect(request.referrer)

        # 4. Return as downloadable file
        response = make_response(pdf_file)
        response.headers['Content-Type'] = 'application/pdf'
        filename = f"Invoice_{invoice_data['flat_number']}_{invoice_data['month']}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    except Exception as e:
        flash(f"PDF Generation Failed: {str(e)}", "danger")
        return redirect(request.referrer)
    
@maintenance_bp.route("/mark-paid/<int:m_id>", methods=["POST"])
@login_required
@role_required("treasurer", "admin")
def mark_as_paid_manual(m_id):
    treasurer_id = session["user"]["id"]
    
    try:
        # 1. Update Database
        MaintenanceRepository.mark_as_paid(m_id, method='Cash/Transfer', receiver_id=treasurer_id)

        # 2. Get Data for Invoice
        invoice_data = MaintenanceRepository.get_full_invoice_data(m_id)

        # 3. Generate PDF & Send Email to Resident
        from utils.pdf_helper import generate_pdf_blob
        from utils.mail import send_email_with_pdf
        
        context = {
            "society": {"name": invoice_data['society_name'], "address": invoice_data['society_address']},
            "user": {"full_name": invoice_data['owner_name']},
            "flat": {"flat_number": invoice_data['flat_number'], "block_name": invoice_data['block_name']},
            "maintenance": invoice_data,
            "date_today": datetime.now().strftime('%B %d, %Y')
        }

        pdf_blob = generate_pdf_blob('maintenance/invoice_template.html', context)
        
        # Send to the owner/tenant email
        send_email_with_pdf(
            recipient_email=invoice_data['owner_email'],
            recipient_name=invoice_data['owner_name'],
            pdf_data=pdf_blob,
            filename=f"Receipt_{invoice_data['flat_number']}.pdf",
            maintenance=invoice_data
        )

        flash(f"Payment recorded. Receipt has been sent to {invoice_data['owner_name']}.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(request.referrer)
