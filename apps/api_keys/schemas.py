from ninja import Schema
from typing import List, Optional
from datetime import datetime

from pydantic import Field


class CreateAPIKeySchema(Schema):
    name: str = Field(..., example="wallet-service")
    permissions: List[str] = Field(..., example=["deposit", "transfer", "read"])
    expiry: str = Field(..., example="1M")


class APIKeyResponseSchema(Schema):
    api_key: str
    expires_at: datetime
    name: str
    permissions: List[str]


class APIKeyInfoSchema(Schema):
    """Schema for listing API keys (without showing the actual key)"""

    id: int
    name: str
    prefix: str
    permissions: List[str]
    expires_at: datetime
    is_revoked: bool
    is_expired: bool
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class RolloverAPIKeySchema(Schema):
    """Schema for rolling over an expired API key"""

    expired_key_id: str
    expiry: str  # 1H, 1D, 1M, 1Y

    class Config:
        json_schema_extra = {"example": {"expired_key_id": "123", "expiry": "1M"}}


class RevokeAPIKeySchema(Schema):
    """Schema for revoking an API key"""

    key_id: int


class MessageSchema(Schema):
    """Generic message response"""

    message: str


class ErrorSchema(Schema):
    """Error response schema"""

    detail: str
