from .models import APIKey


class PermissionValidator:
    VALID_PERMISSIONS = {"deposit", "transfer", "read"}

    @staticmethod
    def validate_permission(api_key: APIKey, required_permission: str) -> bool:
        """
        Check if an API key has the required permission
        """
        if required_permission not in PermissionValidator.VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {required_permission}")

        return required_permission in api_key.permissions

    @staticmethod
    def validate_permissions(api_key: APIKey, required_permissions: list[str]) -> bool:
        """
        Check if an API key has all required permissions
        """
        for permission in required_permissions:
            if not PermissionValidator.validate_permission(api_key, permission):
                return False
        return True

    @staticmethod
    def get_missing_permissions(
        api_key: APIKey, required_permissions: list[str]
    ) -> list[str]:
        """
        Get list of missing permissions
        """
        return [p for p in required_permissions if p not in api_key.permissions]
