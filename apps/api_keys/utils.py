import secrets
import hashlib
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA256
    """
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key
    Returns: (full_key, key_hash, prefix)
    """
    prefix = settings.API_KEY_PREFIX
    random_part = secrets.token_urlsafe(settings.API_KEY_LENGTH)
    full_key = f"{prefix}{random_part}"

    key_hash = hash_api_key(full_key)

    display_prefix = full_key[:12]

    return full_key, key_hash, display_prefix


def parse_expiry_to_datetime(expiry: str) -> datetime:
    """
    Convert expiry string to datetime
    Accepts: 1H, 1D, 1M, 1Y
    """
    expiry = expiry.upper().strip()

    if not expiry or len(expiry) < 2:
        raise ValueError("Invalid expiry format. Use: 1H, 1D, 1M, or 1Y")

    try:
        number = int(expiry[:-1])
        unit = expiry[-1]
    except (ValueError, IndexError):
        raise ValueError("Invalid expiry format. Use: 1H, 1D, 1M, or 1Y")

    now = timezone.now()

    if unit == "H":
        return now + timedelta(hours=number)
    elif unit == "D":
        return now + timedelta(days=number)
    elif unit == "M":
        return now + timedelta(days=number * 30)
    elif unit == "Y":
        return now + timedelta(days=number * 365)
    else:
        raise ValueError(
            "Invalid expiry unit. Use: H (hour), D (day), M (month), or Y (year)"
        )


def validate_permissions(permissions: list[str]) -> None:
    """
    Validate that permissions are valid
    """
    valid_permissions = {"deposit", "transfer", "read"}
    invalid = set(permissions) - valid_permissions

    if invalid:
        raise ValueError(
            f"Invalid permissions: {', '.join(invalid)}. Valid options: {', '.join(valid_permissions)}"
        )

    if not permissions:
        raise ValueError("At least one permission is required")
