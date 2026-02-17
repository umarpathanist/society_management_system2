from permissions.repository import PermissionRepository


class PermissionService:
    """
    Handles permission checks for users
    """

    @staticmethod
    def user_has_permission(user_id, permission_code):
        return PermissionRepository.user_has_permission(
            user_id=user_id,
            permission_code=permission_code
        )
