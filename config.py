import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class Config:
    # 1. SECRET_KEY MUST be inside the class.
    # 2. It MUST be uppercase.
    # 3. We add a long random string as a fallback so it NEVER is None.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'society_management_super_secret_key_998877')

    # Email Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'umarpathanist@gmail.com' 
    MAIL_PASSWORD = 'hiamihhtqusafkry'
    MAIL_DEFAULT_SENDER = 'umarpathanist@gmail.com'    


    RAZORPAY_KEY_ID=os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_RHmKLA3jf1WkPe')
    RAZORPAY_KEY_SECRET=os.environ.get('RAZORPAY_KEY_SECRET', 'DIYXpaetUTEu0oQkHVU56WOL')
    

# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=true
# MAIL_USERNAME=umarpathanist@gmail.com
# MAIL_PASSWORD=hiamihhtqusafkry
# MAIL_DEFAULT_SENDER=Society Management <umarpathanist@gmail.com>
