import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, session

# 1. Import Configuration and Extensions
from config import Config
from extensions import mail
from flask_apscheduler import APScheduler

# 2. Import Blueprints
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from flats.routes import flats_bp
from blocks.routes import blocks_bp
from societies.routes import societies_bp
from admin.routes import admin_bp
from maintenance.routes import maintenance_bp
from owners.routes import owners_bp
from treasurers.routes import treasurers_bp
from income.routes import income_bp
from expenses.routes import expenses_bp
from reports.routes import reports_bp
from notifications.routes import notifications_bp
from tickets.routes import tickets_bp

# 3. Import Context Processors & Automation
from utils.context import load_sidebar_blocks, inject_current_user
from utils.scheduler import auto_generate_maintenance, check_ticket_sla

# Load environment variables
load_dotenv()

# Initialize Scheduler object outside factory
scheduler = APScheduler()

def create_app():
    """Application Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    mail.init_app(app)
    
    # --- CONTEXT PROCESSORS ---
    @app.context_processor
    def inject_notifications():
        user = session.get("user")
        if user:
            try:
                from notifications.repository import NotificationRepository
                count = NotificationRepository.get_unread_count(user["id"])
                return dict(unread_notif_count=count)
            except Exception:
                return dict(unread_notif_count=0)
        return dict(unread_notif_count=0)

    app.context_processor(load_sidebar_blocks)
    app.context_processor(inject_current_user)

    # --- REGISTER BLUEPRINTS ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(flats_bp)
    app.register_blueprint(blocks_bp)
    app.register_blueprint(societies_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(owners_bp)
    app.register_blueprint(treasurers_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(tickets_bp)

    # --- SCHEDULER SETUP ---
    scheduler.init_app(app)
    
    # Only start scheduler if not in testing mode
    if not app.config.get('TESTING', False):
        scheduler.start()
    else:
        # For testing, try to shut down any existing scheduler
        try:
            if scheduler.running:
                scheduler.shutdown(wait=False)
        except:
            pass

    # Define Automated Tasks inside create_app so they have access to 'app'
    # 1. Monthly Maintenance Job
    @scheduler.task('cron', id='do_monthly_maint', day='1', hour='0', minute='1')
    def scheduled_maint():
        from utils.scheduler import auto_generate_maintenance
        auto_generate_maintenance(app)

    # 2. Weekly Report Job (Every Monday)
    @scheduler.task('cron', id='weekly_reports', day_of_week='mon', hour='9', minute='0')
    def weekly_job():
        # Correct the import name to match the function in scheduler.py
        from utils.scheduler import email_scheduled_reports
        email_scheduled_reports(app)

    @scheduler.task('interval', id='do_sla_check', hours=6)
    def scheduled_sla():
        check_ticket_sla(app)

    # Root Route
    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app

# Initialize the final app object
app = create_app()

if __name__ == "__main__":
    # use_reloader=False is mandatory when using APScheduler
    app.run(host="0.0.0.0", port=8001, debug=True, use_reloader=False)
