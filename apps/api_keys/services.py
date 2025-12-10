from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .models import APIKey
from .utils import (
    generate_api_key,
    hash_api_key,
    parse_expiry_to_datetime,
    validate_permissions,
)
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys"""

    MAX_ACTIVE_KEYS = 5

    @staticmethod
    def count_active_keys(user: User) -> int:
        """Count active (non-expired, non-revoked) keys for a user"""
        now = timezone.now()
        return APIKey.objects.filter(
            user=user, is_revoked=False, expires_at__gt=now
        ).count()

    @staticmethod
    @transaction.atomic
    def create_api_key(
        user: User, name: str, permissions: list[str], expiry: str
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key for a user
        Returns: (APIKey instance, plain_key)
        """
        validate_permissions(permissions)

        active_count = APIKeyService.count_active_keys(user)
        if active_count >= APIKeyService.MAX_ACTIVE_KEYS:
            raise ValueError(
                f"Maximum of {APIKeyService.MAX_ACTIVE_KEYS} active API keys allowed"
            )

        expires_at = parse_expiry_to_datetime(expiry)

        plain_key, key_hash, prefix = generate_api_key()

        api_key = APIKey.objects.create(
            user=user,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            permissions=permissions,
            expires_at=expires_at,
        )

        logger.info(f"API key created for user {user.email}: {name}")

        return api_key, plain_key

    @staticmethod
    def validate_api_key(key: str) -> Optional[APIKey]:
        """
        Validate an API key and return the APIKey instance if valid
        Returns None if invalid
        """
        key_hash = hash_api_key(key)

        try:
            api_key = APIKey.objects.select_related("user").get(
                key_hash=key_hash, is_revoked=False
            )

            if api_key.is_expired:
                logger.warning(f"Expired API key used: {api_key.prefix}")
                return None

            api_key.update_last_used()

            return api_key

        except APIKey.DoesNotExist:
            logger.warning("Invalid API key attempted")
            return None

    @staticmethod
    def check_permission(api_key: APIKey, required_permission: str) -> bool:
        """
        Check if an API key has the required permission
        """
        return required_permission in api_key.permissions

    @staticmethod
    @transaction.atomic
    def rollover_api_key(
        user: User, expired_key_id: str, new_expiry: str
    ) -> Tuple[APIKey, str]:
        """
        Rollover an expired API key with the same permissions
        Returns: (new APIKey instance, plain_key)
        """
        try:
            old_key = APIKey.objects.get(id=expired_key_id, user=user)
        except APIKey.DoesNotExist:
            raise ValueError("API key not found or does not belong to you")

        if not old_key.is_expired:
            raise ValueError("Can only rollover expired keys")

        active_count = APIKeyService.count_active_keys(user)
        if active_count >= APIKeyService.MAX_ACTIVE_KEYS:
            raise ValueError(
                f"Maximum of {APIKeyService.MAX_ACTIVE_KEYS} active API keys allowed"
            )

        # Create new key with same permissions
        new_key, plain_key = APIKeyService.create_api_key(
            user=user,
            name=old_key.name,
            permissions=old_key.permissions,
            expiry=new_expiry,
        )

        logger.info(f"API key rolled over for user {user.email}: {old_key.name}")

        return new_key, plain_key

    @staticmethod
    def revoke_api_key(user: User, key_id: int) -> None:
        """
        Revoke an API key
        """
        try:
            api_key = APIKey.objects.get(id=key_id, user=user)
        except APIKey.DoesNotExist:
            raise ValueError("API key not found or does not belong to you")

        if api_key.is_revoked:
            raise ValueError("API key is already revoked")

        api_key.revoke()
        logger.info(f"API key revoked for user {user.email}: {api_key.name}")

    @staticmethod
    def list_user_keys(user: User) -> list[APIKey]:
        """
        List all API keys for a user
        """
        return list(APIKey.objects.filter(user=user).order_by("-created_at"))
