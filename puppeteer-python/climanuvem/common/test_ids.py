"""Stable ``data-testid`` values of the React Native frontend (``testID`` prop).

Mirrors ``playwright-csharp/Common/TestIds.cs`` and is kept in sync with
``sut/frontend``. Build selectors with ``TestId.of(Login.EMAIL_INPUT)``.
Previous stack screens stay mounted but hidden, so the same id can exist on
several mounted screens; the browser layer waits for the first match to be visible.
"""


class Welcome:
    TITLE = "welcome-title"
    TAGLINE = "welcome-tagline"
    LOGIN_BUTTON = "welcome-login-button"
    GUEST_BUTTON = "welcome-guest-button"
    FEEDBACK = "welcome-feedback"


class Login:
    BACK_BUTTON = "login-back-button"
    EMAIL_INPUT = "login-email-input"
    PASSWORD_INPUT = "login-password-input"
    PASSWORD_TOGGLE = "login-password-toggle"
    SUBMIT_BUTTON = "login-submit-button"
    GOOGLE_BUTTON = "login-google-button"
    FORGOT_PASSWORD_LINK = "login-forgot-password-link"
    REGISTER_LINK = "login-register-link"
    FEEDBACK = "login-feedback"


class Register:
    BACK_BUTTON = "register-back-button"
    USERNAME_INPUT = "register-username-input"
    EMAIL_INPUT = "register-email-input"
    PASSWORD_INPUT = "register-password-input"
    PASSWORD_TOGGLE = "register-password-toggle"
    CONFIRM_PASSWORD_INPUT = "register-confirm-password-input"
    CONFIRM_PASSWORD_TOGGLE = "register-confirm-password-toggle"
    SUBMIT_BUTTON = "register-submit-button"
    LOGIN_LINK = "register-login-link"
    FEEDBACK = "register-feedback"


class Home:
    TITLE = "home-title"
    WELCOME = "home-welcome"
    ANALYZE_CARD = "home-analyze-card"
    HISTORY_CARD = "home-history-card"
    LOGOUT_CARD = "home-logout-card"


class Capture:
    BACK_BUTTON = "capture-back-button"
    HEADER = "capture-header"
    CAMERA_CARD = "capture-camera-card"
    GALLERY_CARD = "capture-gallery-card"
    EXPLAINABILITY = "capture-explainability"
    EXPLAINABILITY_SWITCH = "capture-explainability-switch"
    EXPLAINABILITY_WARNING = "capture-explainability-warning"
    FORMATS_INFO = "capture-formats-info"
    FEEDBACK = "capture-feedback"


class Profile:
    BACK_BUTTON = "profile-back-button"
    TITLE = "profile-title"
    EMAIL = "profile-email"
    GUEST_PREFERENCES = "profile-guest-preferences"
    USERNAME_SECTION = "profile-username-section"
    USERNAME_INPUT = "profile-username-input"
    SAVE_BUTTON = "profile-save-button"
    DELETE_ACCOUNT_BUTTON = "profile-delete-account-button"
    DELETE_CONFIRM_BUTTON = "profile-delete-confirm-button"
    DELETE_CANCEL_BUTTON = "profile-delete-cancel-button"
    THEME_LIGHT = "profile-theme-light"
    THEME_DARK = "profile-theme-dark"
    THEME_SYSTEM = "profile-theme-system"
    LANGUAGE_ENGLISH = "profile-language-english"
    LANGUAGE_SPANISH = "profile-language-spanish"
    LANGUAGE_SYSTEM = "profile-language-system"
    FEEDBACK = "profile-feedback"


class Dialog:
    """Shared StatusModal ids; only one dialog is mounted at a time."""

    TITLE = "dialog-title"
    MESSAGE = "dialog-message"
    ACCEPT_BUTTON = "dialog-accept-button"
    CONFIRM_BUTTON = "dialog-confirm-button"
    CANCEL_BUTTON = "dialog-cancel-button"
