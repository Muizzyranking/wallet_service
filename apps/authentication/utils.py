from ninja_jwt.tokens import RefreshToken
from django.contrib.auth.models import User
from typing import Dict


def generate_tokens_for_user(user: User) -> Dict[str, str]:
    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def get_user_data(user: User) -> dict:
    profile = user.profile
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "wallet_number": profile.wallet_number,
        "profile_picture": profile.profile_picture,
    }
