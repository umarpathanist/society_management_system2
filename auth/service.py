from werkzeug.security import check_password_hash
from auth.repository import AuthRepository


class AuthService:
    """
    Handles authentication and login logic
    """

    # auth/service.py
class AuthService:
    @staticmethod
    def authenticate(email, password):
        user = AuthRepository.get_user_by_email(email)
        if not user:
            return None, "User not found"
        
        if check_password_hash(user['password_hash'], password):
            # Make sure you are returning the WHOLE 'user' object here
            return user, None
        
        return None, "Invalid password"
    

    from werkzeug.security import check_password_hash
from auth.repository import UserRepository

class AuthService:
    @staticmethod
    def authenticate(email, password):
        user = UserRepository.get_by_email(email)
        if not user:
            return None, "User not found"
        
        if not check_password_hash(user['password_hash'], password):
            return None, "Invalid password"
            
        return user, None