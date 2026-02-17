# from tenants.repository import tenantRepository
# from flats.repository import FlatRepository


# class tenantService:

#     @staticmethod
#     def get_all():
#         """
#         Fetch all tenants with flat details
#         """
#         return tenantRepository.get_all()

#     @staticmethod
#     def get_by_id(tenant_id):
#         return tenantRepository.get_by_id(tenant_id)

#     @staticmethod
#     def create(data):
#         """
#         Create tenant and mark flat as occupied
#         """
#         tenant_id = tenantRepository.create(data)

#         # Mark flat as occupied
#         if data.get("flat_id"):
#             FlatRepository.mark_occupied(data["flat_id"])

#         return tenant_id

#     @staticmethod
#     def update(tenant_id, data):
#         return tenantRepository.update(tenant_id, data)

#     @staticmethod
#     def delete(tenant_id):
#         """
#         Delete tenant and free the flat
#         """
#         flat_id = tenantRepository.get_flat_id(tenant_id)

#         if flat_id:
#             FlatRepository.mark_vacant(flat_id)

#         return tenantRepository.delete(tenant_id)

#     @staticmethod
#     def get_vacant_flats():
#         """
#         Used in Create tenant dropdown
#         """
#         return FlatRepository.get_vacant_flats()
