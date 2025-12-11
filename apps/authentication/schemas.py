from ninja import Schema
from typing import Optional


class UserProfileSchema(Schema):
    """Complete user profile with wallet details"""

    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    wallet_number: str
    profile_picture: Optional[str] = None
    wallet_balance: int  # In kobo
    created_at: str


class GoogleAuthURLSchema(Schema):
    authorization_url: str


class UserSchema(Schema):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    wallet_number: str
    profile_picture: Optional[str] = None


class TokenResponseSchema(Schema):
    access: str
    refresh: str
    token_type: str = "Bearer"
    user: UserSchema


class GoogleCallbackSchema(Schema):
    code: str
    state: Optional[str] = None


class ErrorSchema(Schema):
    detail: str
