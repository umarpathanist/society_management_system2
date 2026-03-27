import calendar
from datetime import datetime
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session, jsonify
from dateutil.relativedelta import relativedelta
from extensions import get_razorpay_client
from utils.decorators import login_required, role_required

# Repositories
from treasurers.service import TreasurerService
from societies.repository import SocietyRepository
from flats.repository import FlatRepository
from maintenance.repository import MaintenanceRepository
from notifications.repository import NotificationRepository
from database.connection import get_db_connection
from utils.mail import send_maintenance_reminder, send_payment_received_to_resident, send_payment_confirmation_to_treasurer

treasurers_bp = Blueprint("treasurers", __name__, url_prefix="/treasurers")

# --- MONTH HELPER MAPS ---
MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}
REV_MONTH_MAP = {v: k for k, v in MONTH_MAP.items()}

# ---------------------------------------------------------
# HELPER: fetch resident info for a flat
# ---------------------------------------------------------
def _get_flat_resident(flat_id):
    """Returns (email, name, flat_number) for the flat's tenant or owner."""
    conn = get_db_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT
                f.flat_number,
                COALESCE(ut.email,     uo.email)     as email,
                COALESCE(ut.full_name, uo.full_name) as full_name
            FROM flats f
            LEFT JOIN users uo ON f.owner_id  = uo.id
            LEFT JOIN users ut ON f.tenant_id = ut.id
            WHERE f.id = %s
        """, (flat_id,))
        return cur.fetchone()
    finally:
        cur.close(); conn.close()

# ---------------------------------------------------------
# 1. LIST TREASURERS
# ---------------------------------------------------------
@treasurers_bp.route("/list")
@login_required
@role_required("super_admin")
def list():
    treasurers = TreasurerService.list_all()
    return render_template("treasurers/list.html", treasurers=treasurers)

# ---------------------------------------------------------
# 2. ADD TREASURER
# ---------------------------------------------------------
@treasurers_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "super_admin")
def add():
    user = session.get("user")
    role = user.get("role")

    if request.method == "POST":
        soc_id = request.form.get("society_id") if role == "super_admin" else session.get("society_id")
        try:
            TreasurerService.add_treasurer({
                "full_name":  request.form.get("full_name"),
                "email":      request.form.get("email"),
                "password":   request.form.get("password"),
                "society_id": soc_id
            })
            flash("Treasurer added successfully! ✅", "success")
            return redirect(url_for("treasurers.list") if role == "super_admin" else url_for("societies.list_societies"))
        except ValueError as e:
            flash(str(e), "warning")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    societies = SocietyRepository.get_all() if role == 'super_admin' else []
    return render_template("treasurers/add.html", role=role, societies=societies)

# ---------------------------------------------------------
# 3. EDIT TREASURER
# ---------------------------------------------------------
@treasurers_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("super_admin")
def edit(id):
    treasurer = TreasurerService.get_treasurer(id)
    if not treasurer:
        flash("Treasurer not found", "danger")
        return redirect(url_for("treasurers.list"))

    if request.method == "POST":
        try:
            TreasurerService.update_treasurer(id, {
                "full_name":  request.form.get("full_name"),
                "email":      request.form.get("email"),
                "society_id": request.form.get("society_id"),
                "password":   request.form.get("password")
            })
            flash("Treasurer profile updated! ✅", "success")
            return redirect(url_for("treasurers.list"))
        except Exception as e:
            flash(f"Update Error: {str(e)}", "danger")

    societies = SocietyRepository.get_all()
    return render_template("treasurers/edit.html", treasurer=treasurer, societies=societies)

# ---------------------------------------------------------
# 4. DELETE TREASURER
# ---------------------------------------------------------
@treasurers_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
@role_required("super_admin")
def delete(id):
    TreasurerService.delete_treasurer(id)
    flash("Treasurer removed. ✅", "success")
    return redirect(url_for("treasurers.list"))

# ---------------------------------------------------------
# 5. AJAX HELPERS
# ---------------------------------------------------------
@treasurers_bp.route("/get-occupied-flats/<int:block_id>")
@login_required
def get_occupied_flats(block_id):
    flats = FlatRepository.get_by_block(block_id)
    occupied = [f for f in flats if f.get('owner_name') or f.get('tenant_name')]
    return jsonify({"flats": occupied})


@treasurers_bp.route("/get-next-unpaid/<int:flat_id>")
@login_required
def get_next_unpaid(flat_id):
    bill = MaintenanceRepository.get_next_unpaid_bill(flat_id)
    if bill:
        return jsonify({
            "id":     bill['id'],
            "month":  bill['month'],
            "year":   bill['year'],
            "amount": float(bill['amount'])
        })
    return jsonify({"error": "No unpaid bills"}), 404

# ---------------------------------------------------------
# 6. COLLECT MAINTENANCE (Cash + Online Razorpay)
# ---------------------------------------------------------
@treasurers_bp.route("/collect-maintenance", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "admin", "super_admin")
def collect_maintenance():
    user = session.get("user")
    role = user.get("role", "").lower()
    selected_soc_id = (
        request.args.get("society_id") or request.form.get("society_id")
    ) if role == "super_admin" else session.get("society_id")

    if request.method == "POST":
        flat_id      = request.form.get("flat_id")
        amount       = request.form.get("amount")
        s_month      = request.form.get("start_month")
        s_year       = request.form.get("start_year")
        e_month      = request.form.get("end_month")
        e_year       = request.form.get("end_year")
        payment_mode = request.form.get("payment_mode", "cash")

        if not all([flat_id, amount, s_month, s_year, e_month, e_year]):
            flash("Data missing. Please select a flat and fill all fields.", "warning")
            return redirect(url_for("treasurers.collect_maintenance", society_id=selected_soc_id))

        # ── ONLINE: Create Razorpay order ──
        if payment_mode == "online":
            try:
                start_dt = datetime(int(s_year), MONTH_MAP[s_month], 1)
                end_dt   = datetime(int(e_year),  MONTH_MAP[e_month], 1)
                months   = 0
                curr     = start_dt
                while curr <= end_dt:
                    months += 1
                    curr += relativedelta(months=1)

                total_paise = int(float(amount) * months * 100)
                client = get_razorpay_client()
                order  = client.order.create(data={
                    "amount":   total_paise,
                    "currency": "INR",
                    "receipt":  f"maint_{flat_id}_{int(datetime.now().timestamp())}"
                })
                return jsonify({
                    "status":           "order_created",
                    "order_id":         order["id"],
                    "amount":           order["amount"],
                    "key":              current_app.config["RAZORPAY_KEY_ID"],
                    "full_name":        user.get("full_name", ""),
                    "email":            user.get("email", ""),
                    "flat_id":          flat_id,
                    "amount_per_month": amount,
                    "start_month":      s_month,
                    "start_year":       s_year,
                    "end_month":        e_month,
                    "end_year":         e_year,
                })
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        # ── CASH: Process and send emails ──
        try:
            start_dt = datetime(int(s_year), MONTH_MAP[s_month], 1)
            end_dt   = datetime(int(e_year),  MONTH_MAP[e_month], 1)
            curr     = start_dt
            count    = 0

            while curr <= end_dt:
                m_name = REV_MONTH_MAP[curr.month]
                y_num  = curr.year
                bill   = MaintenanceRepository.get_by_flat_id_month_year(flat_id, m_name, y_num)
                if not bill:
                    MaintenanceRepository.bulk_create_maintenance(
                        [flat_id], float(amount), m_name, y_num, curr.strftime('%Y-%m-10')
                    )
                MaintenanceRepository.mark_as_paid_manually(flat_id, m_name, y_num)
                curr += relativedelta(months=1)
                count += 1

            # Send emails
            resident = _get_flat_resident(flat_id)
            if resident and resident.get("email"):
                period = f"{s_month} {s_year}" if (s_month == e_month and s_year == e_year) \
                         else f"{s_month} {s_year} – {e_month} {e_year}"
                total_amount = float(amount) * count
                send_payment_received_to_resident(
                    recipient_email = resident["email"],
                    recipient_name  = resident["full_name"],
                    amount          = total_amount,
                    month           = period,
                    year            = "",
                    payment_method  = "Cash",
                    flat_number     = resident["flat_number"]
                )

            treasurer_email = user.get("email")
            if treasurer_email:
                send_payment_confirmation_to_treasurer(
                    treasurer_email = treasurer_email,
                    treasurer_name  = user.get("full_name", "Treasurer"),
                    resident_name   = resident["full_name"] if resident else "Resident",
                    flat_number     = resident["flat_number"] if resident else flat_id,
                    amount          = float(amount) * count,
                    month           = f"{s_month} {s_year}" if (s_month == e_month and s_year == e_year) \
                                      else f"{s_month} {s_year} – {e_month} {e_year}",
                    year            = "",
                    payment_method  = "Cash"
                )

            flash(f"✅ Cash payment for {count} month(s) recorded! Emails sent.", "success")
            return redirect(url_for("dashboard.index_redirect"))

        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for("treasurers.collect_maintenance", society_id=selected_soc_id))

    # ── GET ──
    societies_data = SocietyRepository.get_all() if role == "super_admin" else []
    blocks_data = []
    if selected_soc_id:
        from blocks.repository import BlockRepository
        blocks_data = BlockRepository.get_by_society(selected_soc_id)

    return render_template(
        "treasurers/collect_maintenance.html",
        societies=societies_data,
        blocks=blocks_data,
        selected_soc=int(selected_soc_id) if selected_soc_id else None,
        role=role,
        now=datetime.now()
    )

# ---------------------------------------------------------
# 7. VERIFY RAZORPAY PAYMENT
# ---------------------------------------------------------
@treasurers_bp.route("/verify-collect-payment", methods=["POST"])
@login_required
def verify_collect_payment():
    import razorpay
    user       = session.get("user")
    data       = request.get_json()
    flat_id    = data.get("flat_id")
    amount     = data.get("amount_per_month")
    s_month    = data.get("start_month")
    s_year     = data.get("start_year")
    e_month    = data.get("end_month")
    e_year     = data.get("end_year")
    payment_id = data.get("razorpay_payment_id")
    order_id   = data.get("razorpay_order_id")
    signature  = data.get("razorpay_signature")

    # 1. Verify signature
    try:
        client = razorpay.Client(
            auth=(current_app.config["RAZORPAY_KEY_ID"],
                  current_app.config["RAZORPAY_KEY_SECRET"])
        )
        client.utility.verify_payment_signature({
            "razorpay_order_id":   order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature":  signature
        })
    except Exception:
        return jsonify({"status": "error", "message": "Signature verification failed"}), 400

    # 2. Mark months as paid
    try:
        start_dt = datetime(int(s_year), MONTH_MAP[s_month], 1)
        end_dt   = datetime(int(e_year),  MONTH_MAP[e_month], 1)
        curr     = start_dt
        count    = 0

        while curr <= end_dt:
            m_name = REV_MONTH_MAP[curr.month]
            y_num  = curr.year
            bill   = MaintenanceRepository.get_by_flat_id_month_year(flat_id, m_name, y_num)
            if not bill:
                MaintenanceRepository.bulk_create_maintenance(
                    [flat_id], float(amount), m_name, y_num, curr.strftime('%Y-%m-10')
                )
                bill = MaintenanceRepository.get_by_flat_id_month_year(flat_id, m_name, y_num)
            if bill:
                MaintenanceRepository.mark_as_paid(
                    bill["id"], method="Online", p_id=payment_id
                )
            curr += relativedelta(months=1)
            count += 1

        # 3. Send emails
        resident     = _get_flat_resident(flat_id)
        period       = f"{s_month} {s_year}" if (s_month == e_month and s_year == e_year) \
                       else f"{s_month} {s_year} – {e_month} {e_year}"
        total_amount = float(amount) * count

        if resident and resident.get("email"):
            send_payment_received_to_resident(
                recipient_email = resident["email"],
                recipient_name  = resident["full_name"],
                amount          = total_amount,
                month           = period,
                year            = "",
                payment_method  = "Online (Razorpay)",
                flat_number     = resident["flat_number"]
            )

        treasurer_email = user.get("email") if user else None
        if treasurer_email:
            send_payment_confirmation_to_treasurer(
                treasurer_email = treasurer_email,
                treasurer_name  = user.get("full_name", "Treasurer"),
                resident_name   = resident["full_name"] if resident else "Resident",
                flat_number     = resident["flat_number"] if resident else flat_id,
                amount          = total_amount,
                month           = period,
                year            = "",
                payment_method  = "Online (Razorpay)"
            )

        flash("Online payment verified and recorded! ✅", "success")
        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------------------------------------
# 8. GENERATE MAINTENANCE
# ---------------------------------------------------------
@treasurers_bp.route("/generate-maintenance", methods=["GET", "POST"])
@login_required
@role_required("treasurer", "super_admin")
def generate_maintenance():
    user           = session.get("user")
    role           = user.get("role").lower()
    session_soc_id = session.get("society_id")

    if request.method == "POST":
        action            = request.form.get("action")
        target_society_id = request.form.get("society_id") if role == "super_admin" else session_soc_id

        if not target_society_id:
            flash("Please select a target society first.", "warning")
            return redirect(url_for("treasurers.generate_maintenance"))

        try:
            from notifications.repository import NotificationRepository
        except ImportError:
            NotificationRepository = None

        conn = get_db_connection()
        cur  = conn.cursor()

        try:
            # ACTION 1: GENERATE BILLS
            if action == "generate":
                amount   = request.form.get("amount")
                month    = request.form.get("month")
                year     = request.form.get("year")
                due_date = request.form.get("due_date")

                if not all([amount, month, year, due_date]):
                    flash("Missing billing details. Please fill all fields.", "danger")
                else:
                    occupied_flats = FlatRepository.get_occupied_by_society(target_society_id)
                    if not occupied_flats:
                        flash("No occupied flats found.", "warning")
                    else:
                        flat_ids = [f['id'] for f in occupied_flats]

                        # Generate bills
                        MaintenanceRepository.bulk_create_maintenance(
                            flat_ids, float(amount), month, int(year), due_date
                        )

                        # ✅ FIXED: MySQL IN() instead of PostgreSQL ANY()
                        placeholders = ','.join(['%s'] * len(flat_ids))
                        cur.execute(f"""
                            SELECT DISTINCT
                                COALESCE(ut.email, uo.email) as email,
                                COALESCE(ut.full_name, uo.full_name) as full_name,
                                COALESCE(f.tenant_id, f.owner_id) as user_id
                            FROM flats f
                            LEFT JOIN users uo ON f.owner_id  = uo.id
                            LEFT JOIN users ut ON f.tenant_id = ut.id
                            WHERE f.id IN ({placeholders})
                              AND (f.tenant_id IS NOT NULL OR f.owner_id IS NOT NULL)
                        """, flat_ids)

                        recipients = cur.fetchall()
                        count = 0
                        for r in recipients:
                            if r['email']:
                                send_maintenance_reminder(
                                    r['email'], r['full_name'], amount, month, year
                                )
                                if NotificationRepository:
                                    NotificationRepository.create(
                                        user_id   = r['user_id'],
                                        title     = "New Bill Generated 🧾",
                                        message   = f"Maintenance of ₹{amount} for {month} {year} is generated. Due: {due_date}",
                                        notif_type= "due"
                                    )
                                count += 1
                        flash(f"Bills generated and {count} residents notified! ✅", "success")

            # ACTION 2: SEND REMINDERS
            elif action == "remind":
                cur.execute("""
                    SELECT
                        COALESCE(ut.email, uo.email) as email,
                        COALESCE(ut.full_name, uo.full_name) as full_name,
                        m.amount, m.month, m.year
                    FROM maintenance m
                    JOIN flats f  ON m.flat_id    = f.id
                    JOIN blocks b ON f.block_id   = b.id
                    LEFT JOIN users uo ON f.owner_id  = uo.id
                    LEFT JOIN users ut ON f.tenant_id = ut.id
                    WHERE b.society_id = %s
                      AND m.status = 'unpaid'
                      AND (ut.email IS NOT NULL OR uo.email IS NOT NULL)
                """, (target_society_id,))
                pending = cur.fetchall()
                for p in pending:
                    send_maintenance_reminder(
                        p['email'], p['full_name'], p['amount'], p['month'], p['year']
                    )
                flash(f"Sent {len(pending)} reminders! 📩", "info")

            return redirect(url_for("dashboard.index_redirect"))

        except Exception as e:
            flash(f"Process failed: {str(e)}", "danger")
            if conn: conn.rollback()
        finally:
            cur.close()
            conn.close()

    societies_list = SocietyRepository.get_all() if role == "super_admin" else []
    return render_template(
        "treasurers/generate_maintenance.html",
        societies=societies_list,
        role=role,
        now=datetime.now()
    )