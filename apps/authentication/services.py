from typing import Tuple

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import User
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .models import UserProfile


class GoogleOAuthService:
    """Service for handling Google OAuth authentication"""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, state: str = None) -> str:
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Get user information from Google"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    def verify_id_token(self, token: str) -> dict:
        """Verify Google ID token"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), self.client_id
            )
            return idinfo
        except ValueError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    @sync_to_async
    def get_or_create_user(self, google_user_info: dict) -> Tuple[User, bool]:
        """
        Get or create user from Google user info
        Returns: (User, created: bool)
        """
        google_id = google_user_info.get("id")
        email = google_user_info.get("email")

        if not email:
            raise ValueError("Email not provided by Google")

        try:
            profile = UserProfile.objects.select_related("user").get(
                google_id=google_id
            )
            return profile.user, False
        except UserProfile.DoesNotExist:
            pass

        try:
            user = User.objects.get(email=email)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.google_id = google_id
            profile.profile_picture = google_user_info.get("picture")
            profile.save()
            return user, False
        except User.DoesNotExist:
            pass

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=google_user_info.get("given_name", ""),
            last_name=google_user_info.get("family_name", ""),
        )

        UserProfile.objects.create(
            user=user,
            google_id=google_id,
            profile_picture=google_user_info.get("picture"),
        )

        return user, True
