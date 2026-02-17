from societies.repository import SocietyRepository
from blocks.repository import BlockRepository
from flats.repository import FlatRepository


class SocietyService:
    """
    Handles all society-related business logic
    """

    # =====================================================
    # USED BY: Admin → Assign Society
    # =====================================================
    @staticmethod
    def get_all():
        return SocietyRepository.get_all()

    # =====================================================
    # LIST SOCIETIES FOR LOGGED-IN USER
    # =====================================================
    @staticmethod
    def get_for_logged_user(user):
        # SUPER ADMIN → all societies
        if user["role"] == "super_admin":
            return SocietyRepository.get_all()

        # ADMIN → assigned societies
        if user["role"] == "admin":
            return SocietyRepository.get_for_admin(user["id"])

        return []

    # =====================================================
    # GET SOCIETY BY ID
    # =====================================================
    @staticmethod
    def get_by_id(society_id):
        return SocietyRepository.get_by_id(society_id)

    # =====================================================
    # CREATE SOCIETY + AUTO BLOCKS & FLATS
    # =====================================================
    @staticmethod
    def create(form):
        society_id = SocietyRepository.create(form)

        total_blocks = int(form.get("total_blocks", 0))
        floors_per_block = int(form.get("floors_per_block", 0))
        flats_per_floor = int(form.get("flats_per_floor", 0))

        for i in range(total_blocks):
            block_letter = chr(65 + i)
            block_id = BlockRepository.create({
                "society_id": society_id,
                "name": f"Block {block_letter}",
                "floors": floors_per_block,
            })

            for floor in range(1, floors_per_block + 1):
                for flat in range(1, flats_per_floor + 1):
                    FlatRepository.create({
                        "block_id": block_id,
                        "flat_number": f"{block_letter}-{floor}{flat:02d}",
                        "floor_number": floor,
                    })

        return society_id

    # =====================================================
    # UPDATE SOCIETY
    # =====================================================
    @staticmethod
    def update(society_id, form):
        SocietyRepository.update(society_id, {
            "name": form.get("name", "").strip(),
            "address": form.get("address", "").strip(),
            "total_blocks": int(form.get("total_blocks", 0)),
            "floors_per_block": int(form.get("floors_per_block", 0)),
            "flats_per_floor": int(form.get("flats_per_floor", 0)),
        })

    # =====================================================
    # DELETE SOCIETY
    # =====================================================
    @staticmethod
    def delete(society_id):
        SocietyRepository.delete(society_id)
