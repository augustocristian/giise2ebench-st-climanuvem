namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Stable <c>data-testid</c> values added to the React Native frontend
/// (<c>testID</c> prop). Use with <c>Page.GetByTestId(...)</c>. Kept in sync
/// with <c>sut/frontend</c>. Previous stack screens stay mounted but hidden,
/// so pick the visible match when an id exists on several mounted screens.
/// </summary>
public static class TestIds
{
    /// <summary>Welcome screen.</summary>
    public static class Welcome
    {
        public const string Title = "welcome-title";
        public const string Tagline = "welcome-tagline";
        public const string LoginButton = "welcome-login-button";
        public const string GuestButton = "welcome-guest-button";
        public const string Feedback = "welcome-feedback";
    }

    /// <summary>Login screen.</summary>
    public static class Login
    {
        public const string BackButton = "login-back-button";
        public const string EmailInput = "login-email-input";
        public const string PasswordInput = "login-password-input";
        public const string PasswordToggle = "login-password-toggle";
        public const string SubmitButton = "login-submit-button";
        public const string GoogleButton = "login-google-button";
        public const string ForgotPasswordLink = "login-forgot-password-link";
        public const string RegisterLink = "login-register-link";
        public const string Feedback = "login-feedback";
    }

    /// <summary>Register screen.</summary>
    public static class Register
    {
        public const string BackButton = "register-back-button";
        public const string UsernameInput = "register-username-input";
        public const string EmailInput = "register-email-input";
        public const string PasswordInput = "register-password-input";
        public const string PasswordToggle = "register-password-toggle";
        public const string ConfirmPasswordInput = "register-confirm-password-input";
        public const string ConfirmPasswordToggle = "register-confirm-password-toggle";
        public const string SubmitButton = "register-submit-button";
        public const string LoginLink = "register-login-link";
        public const string Feedback = "register-feedback";
    }

    /// <summary>Home screen.</summary>
    public static class Home
    {
        public const string Title = "home-title";
        public const string Welcome = "home-welcome";
        public const string AnalyzeCard = "home-analyze-card";
        public const string HistoryCard = "home-history-card";
        public const string LogoutCard = "home-logout-card";
    }

    /// <summary>Capture (analyze image) screen.</summary>
    public static class Capture
    {
        public const string BackButton = "capture-back-button";
        public const string Header = "capture-header";
        public const string CameraCard = "capture-camera-card";
        public const string GalleryCard = "capture-gallery-card";
        public const string Explainability = "capture-explainability";
        public const string ExplainabilitySwitch = "capture-explainability-switch";
        public const string ExplainabilityWarning = "capture-explainability-warning";
        public const string FormatsInfo = "capture-formats-info";
        public const string Feedback = "capture-feedback";
    }

    /// <summary>Profile screen.</summary>
    public static class Profile
    {
        public const string BackButton = "profile-back-button";
        public const string Title = "profile-title";
        public const string Email = "profile-email";
        public const string GuestPreferences = "profile-guest-preferences";
        public const string UsernameSection = "profile-username-section";
        public const string UsernameInput = "profile-username-input";
        public const string SaveButton = "profile-save-button";
        public const string DeleteAccountButton = "profile-delete-account-button";
        public const string DeleteConfirmButton = "profile-delete-confirm-button";
        public const string DeleteCancelButton = "profile-delete-cancel-button";
        public const string ThemeLight = "profile-theme-light";
        public const string ThemeDark = "profile-theme-dark";
        public const string ThemeSystem = "profile-theme-system";
        public const string LanguageEnglish = "profile-language-english";
        public const string LanguageSpanish = "profile-language-spanish";
        public const string LanguageSystem = "profile-language-system";
        public const string Feedback = "profile-feedback";
    }

    /// <summary>Shared status dialog (StatusModal) ids, identical on every screen; only one dialog is mounted at a time.</summary>
    public static class Dialog
    {
        public const string Title = "dialog-title";
        public const string Message = "dialog-message";
        public const string AcceptButton = "dialog-accept-button";
        public const string ConfirmButton = "dialog-confirm-button";
        public const string CancelButton = "dialog-cancel-button";
    }
}
