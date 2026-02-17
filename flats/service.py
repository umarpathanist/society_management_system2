from flats.repository import FlatRepository

class FlatService:

    @staticmethod
    def get_by_block(block_id):
        return FlatRepository.get_by_block(block_id)

    @staticmethod
    def get_by_id(flat_id):
        return FlatRepository.get_by_id(flat_id)

    @staticmethod
    def create(data):
        return FlatRepository.create(data)

    @staticmethod
    def toggle_status(flat_id):
        return FlatRepository.toggle_status(flat_id)

    # flats/service.py

    @staticmethod
    def assign_flat_to_user(flat_id, user_id, user_role):
        flat = FlatRepository.get_by_id(flat_id)
        if not flat:
            raise ValueError("Flat not found")

        # This will now set is_occupied = TRUE for both roles
        FlatRepository.assign_user(flat_id, user_id, user_role)
        return True
    