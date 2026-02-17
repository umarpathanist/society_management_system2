from werkzeug.security import generate_password_hash
from owners.repository import OwnerRepository
from maintenance.repository import MaintenanceRepository
from utils.mail import send_login_details

class OwnerService:
    """
    Consolidated Business Logic for Owners and Tenants.
    Handles user creation, dues calculation, and property details.
    """

    # ---------------------------------------------------------
    # 1. USER CREATION & MANAGEMENT
    # ---------------------------------------------------------
    @staticmethod
    def create_owner_or_tenant(data):
        """
        Hashes default password, saves to DB, and sends login email.
        """
        raw_password = "password123" 
        data["password_hash"] = generate_password_hash(raw_password)
        
        # Ensure role is lowercase for database consistency
        data["role"] = data["role"].lower()
        
        # Save to DB via Repository
        new_user = OwnerRepository.create_user(data)
        
        if new_user:
            # Send welcome email with login details
            try:
                send_login_details(
                    recipient_email=data['email'],
                    recipient_name=data['full_name'],
                    password=raw_password,
                    role=data['role']
                )
            except Exception as e:
                print(f"Service Log: User created, but email failed: {e}")
                
        return new_user

    @staticmethod
    def get_user_details(user_id):
        """Bridge to repository to get user profile."""
        return OwnerRepository.get_by_id(user_id)

    @staticmethod
    def update_user(user_id, data):
        """Bridge to repository to update user profile."""
        return OwnerRepository.update(user_id, data)

    @staticmethod
    def delete_user(user_id):
        """Bridge to repository to remove user."""
        return OwnerRepository.delete(user_id)

    # ---------------------------------------------------------
    # 2. PROPERTY (FLAT) LOGIC
    # ---------------------------------------------------------
    @staticmethod
    def get_my_flats(user_id, role):
        """Fetches list of all flats assigned to a user."""
        return OwnerRepository.get_flats_by_user(user_id, role)

    @staticmethod
    def get_owner_account_summary(user_id, role):
        """
        Calculates total properties and total maintenance due for an owner.
        Shows only Flat Numbers in the display string.
        """
        flats = OwnerRepository.get_flats_by_user(user_id, role)
        if not flats:
            return {
                "total_properties": 0, 
                "flats_display": "None", 
                "total_balance": 0.0, 
                "has_dues": False
            }

        total_unpaid_balance = 0.0
        # List comprehension to get flat numbers only (e.g., A-101, B-202)
        flat_list_names = [flat['flat_number'] for flat in flats]
        
        for flat in flats:
            # Sum up unpaid bills for each property
            balance = MaintenanceRepository.get_unpaid_total_by_flat(flat['id'])
            total_unpaid_balance += balance

        return {
            "total_properties": len(flats),
            "flats_display": ", ".join(flat_list_names),
            "total_balance": total_unpaid_balance,
            "has_dues": total_unpaid_balance > 0
        }

    # ---------------------------------------------------------
    # 3. MAINTENANCE / DUES LOGIC
    # ---------------------------------------------------------
    @staticmethod
    def get_my_maintenance(user_id, role):
        """
        Fetches all maintenance records for all flats assigned to the user.
        Provides a clean 'flat_display' for the UI.
        """
        flats = OwnerRepository.get_flats_by_user(user_id, role)
        if not flats:
            return []

        all_bills = []
        for flat in flats:
            # Get bills for this specific flat
            bills = MaintenanceRepository.get_by_flat_id(flat["id"])
            for bill in bills:
                # Convert RealDictRow to standard dict to add display metadata
                bill_dict = dict(bill)
                bill_dict['flat_display'] = flat['flat_number'] 
                all_bills.append(bill_dict)
        
        return all_bills