# from werkzeug.security import generate_password_hash
# from admin.repository import AdminRepository
# from utils.mail import send_login_details

# class AdminService:
#     @staticmethod
#     def get_admins():
#         return AdminRepository.get_all_admins()

#     @staticmethod
#     def get_by_id(admin_id):
#         return AdminRepository.get_by_id(admin_id)

#     # admin/service.py
    
#     @staticmethod
#     def create_admin(data):
#         """Logic to validate and create admin with email."""
#         # 1. Validation: One Admin per Society
#         society_id = data.get("society_id")
#         if society_id:
#             existing = AdminRepository.get_admin_by_society(society_id)
#             if existing:
#                 raise ValueError(f"This society is already managed by {existing['full_name']}.")

#         # 2. Prepare Data
#         raw_password = data.get("password")
#         data["password_hash"] = generate_password_hash(raw_password)
#         data["role"] = "admin"
        
#         # 3. Save to DB
#         new_id = AdminRepository.create_admin(data)
        
#         # 4. Send Email
#         if new_id:
#             send_login_details(data['email'], data['full_name'], raw_password, "Society Admin")
#         return new_id

#     # ... keep get_admins and delete methods ...

#     @staticmethod
#     def update_admin(admin_id, data):
#         return AdminRepository.update_admin(admin_id, data)

#     @staticmethod
#     def delete_admin(admin_id):
#         return AdminRepository.delete_admin(admin_id)

#     # admin/service.py

#     @staticmethod
#     def assign_society(admin_id, society_id):
#         # 1. CHECK: Does this society already have an admin?
#         existing_admin = AdminRepository.get_admin_by_society(society_id)
        
#         # 2. If someone else is there, block the assignment
#         if existing_admin:
#             raise ValueError(f"This society is already managed by {existing_admin['full_name']}.")

#         # 3. If free, proceed
#         return AdminRepository.assign_society(admin_id, society_id)

#     # ... keep your other methods ...






from werkzeug.security import generate_password_hash
from admin.repository import AdminRepository
from utils.mail import send_login_details

class AdminService:
    @staticmethod
    def get_admins():
        return AdminRepository.get_all_admins()

    @staticmethod
    def get_by_id(admin_id):
        return AdminRepository.get_by_id(admin_id)

    @staticmethod
    def create_admin(data):
        """Checks 1:1 rule, creates admin, and emails credentials."""
        # Check if society is already taken
        society_id = data.get("society_id")
        if society_id:
            existing = AdminRepository.get_admin_by_society(society_id)
            if existing:
                raise ValueError(f"This society is already managed by {existing['full_name']}.")

        raw_password = data.get("password") or "password123"
        data["password_hash"] = generate_password_hash(raw_password)
        
        new_id = AdminRepository.create_admin(data)
        if new_id:
            send_login_details(data['email'], data['full_name'], raw_password, "Society Admin")
        return new_id

    @staticmethod
    def update_admin(admin_id, data):
        """Calls the repository update method we just added."""
        return AdminRepository.update_admin(admin_id, data)

    @staticmethod
    def delete_admin(admin_id):
        return AdminRepository.delete_admin(admin_id)

    @staticmethod
    def assign_society(admin_id, society_id):
        # Prevent assigning to an occupied society
        existing = AdminRepository.get_admin_by_society(society_id)
        if existing:
            raise ValueError(f"Society is already managed by {existing['full_name']}.")
        return AdminRepository.assign_society(admin_id, society_id)