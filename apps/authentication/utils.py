from ninja_jwt.tokens import RefreshToken
from django.contrib.auth.models import User
from typing import Dict
from asgiref.sync import sync_to_async


async def generate_tokens_for_user(user: User) -> Dict[str, str]:
    """
    Generate JWT access and refresh tokens for a user
    Uses django-ninja-jwt's built-in token generation
    """

    @sync_to_async
    def _generate():
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    return await _generate()


@sync_to_async
def get_user_data(user: User) -> dict:
    """Get user data with profile information"""
    profile = user.profile
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "wallet_number": profile.wallet_number,
        "profile_picture": profile.profile_picture,
    }
