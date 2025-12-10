from ninja.security import APIKeyHeader
from django.contrib.auth.models import User
from django.http import HttpRequest
from typing import Optional
from .services import APIKeyService
import logging

logger = logging.getLogger(__name__)


class APIKeyAuth(APIKeyHeader):
    """API Key Authentication for service requests"""

    param_name = "x-api-key"

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[User]:
        if not key:
            return None

        api_key = APIKeyService.validate_api_key(key)
        if not api_key:
            return None

        request.auth_type = "api_key"
        request.api_key = api_key
        request.auth_user = api_key.user

        return api_key.user
