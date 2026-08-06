from app.infrastructure.config import get_settings
from app.infrastructure.firebase_service import verify_token


class InvalidTokenError(ValueError):
    pass


def authenticate_user(token: str):
    settings = get_settings()
    if settings.test_mode and token:
        return {
            "uid": settings.test_user_uid,
            "firebase": {
                "sign_in_provider": "anonymous" if token != settings.test_token else "custom"
            }
        }

    decoded = verify_token(token)
    if not decoded:
        raise InvalidTokenError("Invalid token")
    return decoded
