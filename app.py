# import os
# from dotenv import load_dotenv
# from flask import Flask, redirect, url_for

# # 1. Import Configuration and Extensions
# from config import Config
# from extensions import mail

# from flask_apscheduler import APScheduler
# from utils.scheduler import auto_generate_maintenance

# scheduler = APScheduler()

# # 2. Import Blueprints
# from auth.routes import auth_bp
# from dashboard.routes import dashboard_bp
# from flats.routes import flats_bp
# from blocks.routes import blocks_bp
# from tenants.routes import tenants_bp
# from societies.routes import societies_bp
# from admin.routes import admin_bp
# from maintenance.routes import maintenance_bp
# from payments.routes import payments_bp
# from owners.routes import owners_bp
# from treasurers.routes import treasurers_bp
# from income.routes import income_bp
# from expenses.routes import expenses_bp
# from reports.routes import reports_bp

# # 3. Import Context Processors
# from utils.context import load_sidebar_blocks, inject_current_user

# # Load environment variables
# load_dotenv()

# def create_app():
#     """Application Factory Pattern"""
#     app = Flask(__name__)

#     # Scheduler Configuration
#     scheduler.init_app(app)
#     scheduler.start()

#     # Define the "Job" (Runs on 1st day of every month at 00:00)
#     @scheduler.task('cron', id='do_monthly', day='1', hour='0', minute='0')
#     def scheduled_task():
#         # We pass the 'app' instance here
#         auto_generate_maintenance(app)
        
         
    
#     # Load configuration from Config class in config.py
#     app.config.from_object(Config)

#     # Initialize Extensions
#     mail.init_app(app)

#     # Register All Blueprints
#     app.register_blueprint(auth_bp)
#     app.register_blueprint(dashboard_bp)
#     app.register_blueprint(flats_bp)
#     app.register_blueprint(blocks_bp)
#     app.register_blueprint(tenants_bp)
#     app.register_blueprint(societies_bp)
#     app.register_blueprint(admin_bp)
#     app.register_blueprint(maintenance_bp)
#     app.register_blueprint(payments_bp)
#     app.register_blueprint(owners_bp)
#     app.register_blueprint(treasurers_bp)
#     app.register_blueprint(income_bp)
#     app.register_blueprint(expenses_bp)
#     app.register_blueprint(reports_bp)


#     # Register Context Processors (available in all templates)
#     app.context_processor(load_sidebar_blocks)
#     app.context_processor(inject_current_user)

#     # Root Route Redirection
#     @app.route("/")
#     def home():
#         return redirect(url_for("auth.login"))

#     return app

# if __name__ == "__main__":
#     app = create_app()
#     # Debug mode should be False in production
#     app.run(debug=True)





import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_apscheduler import APScheduler

# 1. Import Configuration and Extensions
from config import Config
from extensions import mail

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

# 3. Import Context Processors & Automation
from utils.context import load_sidebar_blocks, inject_current_user
from utils.scheduler import auto_generate_maintenance

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
    
    # Initialize and Start Scheduler
    scheduler.init_app(app)
    scheduler.start()

    # Define the "Job" (Runs on 1st day of every month at 00:01)
    # FOR TESTING: Use trigger='interval', minutes=1
    @scheduler.task('cron', id='do_monthly_maint', day='1', hour='0', minute='1')
    def scheduled_task():
        # We pass 'app' to allow mailing in background
        auto_generate_maintenance(app)

    # Register All Blueprints
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

    # Register Context Processors
    app.context_processor(load_sidebar_blocks)
    app.context_processor(inject_current_user)

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False) # use_reloader=False prevents double scheduler start