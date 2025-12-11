import logging

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja import Router
from ninja.responses import Response

from apps.core.auth import jwt_auth
from apps.core.exceptions import APIException

from .schemas import (
    ErrorSchema,
    GoogleAuthURLSchema,
    TokenResponseSchema,
    UserProfileSchema,
)
from .services import GoogleOAuthService
from .utils import generate_tokens_for_user, get_user_data

logger = logging.getLogger(__name__)

router = Router(tags=["Auth"])
google_service = GoogleOAuthService()


@router.get("/google", response=GoogleAuthURLSchema, summary="Initiate Google OAuth")
def google_login(request: HttpRequest):
    """
    Return Google OAuth authorization URL (no redirect from backend)
    Frontend should redirect user to this URL
    """
    auth_url = google_service.get_authorization_url()
    return {"authorization_url": auth_url}


@router.get(
    "/google/callback",
    response={200: TokenResponseSchema, 400: ErrorSchema},
    summary="Google OAuth Callback",
)
async def google_callback(request: HttpRequest, code: str, state: str = None):
    """
    Handle Google OAuth callback and return JWT tokens

    - Exchanges authorization code for access token
    - Retrieves user info from Google
    - Creates or retrieves user in database
    - Generates JWT access and refresh tokens
    """
    try:
        # Exchange code for tokens
        logger.info("Exchanging code for token...")
        token_data = await google_service.exchange_code_for_token(code)
        logger.info(f"Token data received: {token_data.keys()}")

        access_token = token_data.get("access_token")

        if not access_token:
            logger.error(f"No access token in response: {token_data}")
            return Response(
                {"detail": "Failed to obtain access token from Google"}, status=400
            )

        # Get user info from Google
        logger.info("Fetching user info from Google...")
        google_user_info = await google_service.get_user_info(access_token)
        logger.info(f"Google user info: {google_user_info}")

        # Get or create user
        logger.info("Creating/fetching user...")
        user, created = await google_service.get_or_create_user(google_user_info)
        logger.info(f"User {'created' if created else 'found'}: {user.email}")

        # Generate JWT tokens
        tokens = await generate_tokens_for_user(user)
        user_data = await get_user_data(user)

        logger.info(f"User {'created' if created else 'logged in'}: {user.email}")

        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "token_type": "Bearer",
            "user": user_data,
        }
    except APIException:
        raise
    except ValueError as e:
        logger.error(f"ValueError in Google callback: {str(e)}", exc_info=True)
        return Response({"detail": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}", exc_info=True)
        return Response({"detail": f"Authentication failed: {str(e)}"}, status=400)


@router.get(
    "/me",
    response={200: UserProfileSchema, 401: ErrorSchema},
    auth=jwt_auth,
    summary="Get Current User Profile",
)
async def get_current_user(request: HttpRequest):
    """
    Get current authenticated user's profile with wallet details

    - Requires JWT authentication
    - Returns user info, wallet number, and balance
    """
    try:

        @sync_to_async
        def get_user_profile():
            from apps.wallet.models import Wallet

            user = request.auth
            profile = user.profile

            # Get or create wallet
            wallet, _ = Wallet.objects.get_or_create(user=user)

            return {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "wallet_number": profile.wallet_number,
                "profile_picture": profile.profile_picture,
                "wallet_balance": wallet.balance,  # In kobo
                "created_at": user.date_joined.isoformat(),
            }

        user_profile = await get_user_profile()
        return user_profile

    except APIException:
        raise

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}", exc_info=True)
        return Response({"detail": "Failed to fetch user profile"}, status=400)
