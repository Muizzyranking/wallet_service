import logging

from django.http import HttpRequest
from ninja import Router
from ninja.responses import Response

from .schemas import ErrorSchema, GoogleAuthURLSchema, TokenResponseSchema
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

    except ValueError as e:
        logger.error(f"ValueError in Google callback: {str(e)}", exc_info=True)
        return Response({"detail": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error in Google callback: {str(e)}", exc_info=True)
        return Response({"detail": f"Authentication failed: {str(e)}"}, status=400)
