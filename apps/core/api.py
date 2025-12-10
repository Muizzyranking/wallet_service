from ninja import NinjaAPI
from ninja_extra.exceptions import NotAuthenticated
from ninja_jwt.exceptions import InvalidToken as NinjaJwtInvalidToken
from ninja.errors import AuthenticationError

from apps.api_keys.api import router as api_keys_router
from apps.authentication.api import router as auth_router
from apps.core.exceptions import APIException
from apps.wallet.api import router as wallet_router

api = NinjaAPI(
    title="Wallet Service API",
    version="1.0.0",
    description="A wallet service with Paystack integration, JWT authentication, and API keys",
)


@api.exception_handler(APIException)
def handle_api_exception(request, exc: APIException):
    return api.create_response(request, {"detail": exc.message}, status=exc.status_code)


@api.exception_handler(NinjaJwtInvalidToken)
@api.exception_handler(NotAuthenticated)
@api.exception_handler(AuthenticationError)
def handle_jwt_exception(request, exc):
    return api.create_response(
        request, {"detail": "Invalid or expired token"}, status=401
    )


api.add_router("/auth/", router=auth_router)
api.add_router("/api-key/", router=api_keys_router)
api.add_router("/wallet/", router=wallet_router)
