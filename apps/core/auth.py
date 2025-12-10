from ninja_jwt.authentication import JWTAuth
from apps.api_keys.authentication import APIKeyAuth

jwt_auth = JWTAuth()
api_key_auth = APIKeyAuth()
jwt_or_api_key_auth = [jwt_auth, api_key_auth]
