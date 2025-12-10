import logging
from typing import List

from apps.core.auth import jwt_auth
from django.http import HttpRequest
from ninja import Router
from ninja.responses import Response

from .schemas import (
    APIKeyInfoSchema,
    APIKeyResponseSchema,
    CreateAPIKeySchema,
    ErrorSchema,
    MessageSchema,
    RevokeAPIKeySchema,
    RolloverAPIKeySchema,
)
from .services import APIKeyService

logger = logging.getLogger(__name__)

router = Router(tags=["API Keys"])


@router.post(
    "/create",
    response={200: APIKeyResponseSchema, 400: ErrorSchema},
    auth=jwt_auth,
    summary="Create API Key",
)
def create_api_key(request: HttpRequest, payload: CreateAPIKeySchema):
    """
    Create a new API key

    - Maximum 5 active keys per user
    - Permissions: deposit, transfer, read
    - Expiry: 1H, 1D, 1M, 1Y
    - Returns the plain API key (only shown once!)
    """
    try:
        api_key, plain_key = APIKeyService.create_api_key(
            user=request.auth,
            name=payload.name,
            permissions=payload.permissions,
            expiry=payload.expiry,
        )

        return {
            "api_key": plain_key,
            "expires_at": api_key.expires_at,
            "name": api_key.name,
            "permissions": api_key.permissions,
        }

    except ValueError as e:
        logger.error(f"Error creating API key: {str(e)}")
        return Response({"detail": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error creating API key: {str(e)}", exc_info=True)
        return Response({"detail": "Failed to create API key"}, status=400)


@router.post(
    "/rollover",
    response={200: APIKeyResponseSchema, 400: ErrorSchema},
    auth=jwt_auth,
    summary="Rollover Expired API Key",
)
def rollover_api_key(request: HttpRequest, payload: RolloverAPIKeySchema):
    """
    Create a new API key using the same permissions as an expired key

    - The expired key must be truly expired
    - The new key reuses the same permissions
    - Returns the plain API key (only shown once!)
    """
    try:
        new_key, plain_key = APIKeyService.rollover_api_key(
            user=request.auth,
            expired_key_id=payload.expired_key_id,
            new_expiry=payload.expiry,
        )

        return {
            "api_key": plain_key,
            "expires_at": new_key.expires_at,
            "name": new_key.name,
            "permissions": new_key.permissions,
        }

    except ValueError as e:
        logger.error(f"Error rolling over API key: {str(e)}")
        return Response({"detail": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error rolling over API key: {str(e)}", exc_info=True)
        return Response({"detail": "Failed to rollover API key"}, status=400)


@router.get(
    "/list", response=List[APIKeyInfoSchema], auth=jwt_auth, summary="List All API Keys"
)
def list_api_keys(request: HttpRequest):
    """
    List all API keys for the authenticated user

    - Does not show the actual key (only prefix)
    - Shows expiration status and permissions
    """
    keys = APIKeyService.list_user_keys(request.auth)

    return [
        {
            "id": key.id,
            "name": key.name,
            "prefix": key.prefix,
            "permissions": key.permissions,
            "expires_at": key.expires_at,
            "is_revoked": key.is_revoked,
            "is_expired": key.is_expired,
            "is_active": key.is_active,
            "created_at": key.created_at,
            "last_used_at": key.last_used_at,
        }
        for key in keys
    ]


@router.post(
    "/revoke",
    response={200: MessageSchema, 400: ErrorSchema},
    auth=jwt_auth,
    summary="Revoke API Key",
)
def revoke_api_key(request: HttpRequest, payload: RevokeAPIKeySchema):
    """
    Revoke an API key

    - Once revoked, the key cannot be used
    - This action cannot be undone
    """
    try:
        APIKeyService.revoke_api_key(user=request.auth, key_id=payload.key_id)

        return {"message": "API key revoked successfully"}

    except ValueError as e:
        logger.error(f"Error revoking API key: {str(e)}")
        return Response({"detail": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error revoking API key: {str(e)}", exc_info=True)
        return Response({"detail": "Failed to revoke API key"}, status=400)
