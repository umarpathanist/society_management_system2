from notifications.repository import NotificationRepository
from utils.mail import send_maintenance_reminder # existing helper

class NotificationService:
    @staticmethod
    def notify(user_id, title, message, notif_type="system", email=None):
        """Unified method to send App and optionally Email notifications."""
        
        # 1. Store in-app notification
        NotificationRepository.create(user_id, title, message, notif_type)
        
        # 2. Logic for Email (Add your preference check here later)
        # if email: send_email_helper(...)