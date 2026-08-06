import logging
from firebase_admin import credentials, initialize_app, auth
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
_firebase_enabled = bool(settings.firebase_key_path) and not settings.test_mode

if _firebase_enabled:
    cred = credentials.Certificate(settings.firebase_key_path)
    initialize_app(cred)
elif settings.test_mode:
    logger.info("Firebase initialization skipped because TEST_MODE=true")
else:
    raise ValueError("FIREBASE_KEY_PATH environment variable is not set. Please check your .env file.")

def verify_token(token: str):
    if not _firebase_enabled:
        logger.warning("Firebase token verification requested while Firebase is disabled")
        return None

    try:
        decoded_token = auth.verify_id_token(
            token,
            clock_skew_seconds=get_settings().firebase_clock_skew_seconds,
        )
        return decoded_token
    except Exception as e:
        logger.exception("Error verifying Firebase token: %s", e)
        return None
