using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Page Object for the Login form. <see cref="CreateAsync"/> waits until
/// the email input is visible. Mirrors selenium-java's <c>LoginPage</c>.
/// </summary>
public sealed class LoginPage : BasePage
{
    private static readonly string[] FeedbackKeywords = ["error", "incorrect", "credencial", "obligatorio", "requerid"];

    private const string EmailPlaceholder = "Correo electrónico";
    private const string PasswordPlaceholder = "Contraseña";
    private const string ForgotPasswordText = "Olvidaste tu contraseña";
    private const string RegisterLinkText = "Regístrate";
    private const string SubmitText = "Iniciar Sesión";
    private const string GoogleText = "Google";
    private const string HomeMarkerText = "Bienvenido";

    private LoginPage(IPage page) : base(page)
    {
    }

    public static async Task<LoginPage> CreateAsync(IPage page)
    {
        var loginPage = new LoginPage(page);
        await WaitForAsync(loginPage.EmailInput());
        return loginPage;
    }

    // ── Queries ──────────────────────────────────────────────────────────

    public Task<bool> IsEmailInputPresentAsync() => IsPresentAsync(EmailInput());
    public Task<bool> IsPasswordInputPresentAsync() => IsPresentAsync(PasswordInput());
    public Task<bool> IsForgotPasswordPresentAsync() => IsPresentAsync(ByPartialText(ForgotPasswordText));
    public Task<bool> IsRegisterLinkPresentAsync() => IsPresentAsync(ByPartialText(RegisterLinkText));
    public Task<bool> IsGoogleLoginPresentAsync() => IsPresentAsync(ByPartialText(GoogleText));
    public Task<bool> IsHomeVisibleAsync() => IsPresentAsync(ByPartialText(HomeMarkerText));
    public Task<string> GetEmailValueAsync() => InputValueAsync(EmailInput());

    public async Task<bool> HasLoginErrorOrValidationAsync() =>
        await BodyTextContainsAnyAsync(FeedbackKeywords) || await HasInvalidRequiredInputAsync();

    // ── Actions ──────────────────────────────────────────────────────────

    public async Task<LoginPage> EnterEmailAsync(string email)
    {
        await FillAsync(EmailInput(), email);
        return this;
    }

    public async Task<LoginPage> EnterPasswordAsync(string password)
    {
        await FillAsync(PasswordInput(), password);
        return this;
    }

    /// <summary>Submits the email/password login form and stays on this page object.</summary>
    public async Task<LoginPage> SubmitLoginAsync()
    {
        await ClickLastVisibleAsync(SubmitButton());
        return this;
    }

    /// <summary>Fills both fields and submits the email/password login form.</summary>
    public async Task<LoginPage> LoginAsync(string email, string password)
    {
        await EnterEmailAsync(email);
        await EnterPasswordAsync(password);
        return await SubmitLoginAsync();
    }

    /// <summary>Waits until the authenticated Home screen is visible and returns its page object.</summary>
    public async Task<HomePage> WaitForHomeAsync()
    {
        try
        {
            await WaitUntilAsync(LoginSettledPredicate());
        }
        catch (PlaywrightException ex)
        {
            throw new InvalidOperationException(
                "Login did not reach Home before timeout. Check account credentials in ACCOUNTS_FILE.", ex);
        }

        if (!await IsHomeVisibleAsync())
        {
            throw new InvalidOperationException(
                "Login failed before reaching Home. Check account credentials in ACCOUNTS_FILE.");
        }
        return await HomePage.CreateAsync(Page);
    }

    /// <summary>Waits until the login attempt is rejected by UI validation or an error message.</summary>
    public async Task<LoginPage> WaitForLoginFailureAsync()
    {
        var predicate =
            "() => {"
            + $"const lower = document.body.innerText.toLowerCase();"
            + $"const feedback = {KeywordsJsArray(FeedbackKeywords)}.some(k => lower.includes(k));"
            + "const invalid = Array.from(document.querySelectorAll('input'))"
            + ".some(el => el.required && !el.checkValidity());"
            + $"const emailPresent = !!document.querySelector('input[placeholder=\"{EmailPlaceholder}\"]');"
            + "return (feedback || invalid) && emailPresent;"
            + "}";
        await WaitUntilAsync(predicate);
        return this;
    }

    public async Task<LoginPage> CloseLoginFeedbackIfPresentAsync()
    {
        var acceptButton = InteractiveWithAnyText("Aceptar", "Accept", "OK");
        if (await IsVisibleAsync(acceptButton))
        {
            await ClickLastVisibleAsync(acceptButton);
        }
        return this;
    }

    /// <summary>
    /// Starts the Google provider flow without requiring credentials. The
    /// flow is considered started when a provider popup opens or the
    /// current page URL/body contains a Google/Firebase identity marker.
    /// </summary>
    public async Task<bool> ClickGoogleLoginStartsProviderAsync()
    {
        try
        {
            await Page.RunAndWaitForPopupAsync(
                async () => await ClickAsync(GoogleButton()),
                new PageRunAndWaitForPopupOptions { Timeout = 5_000 });
            return true;
        }
        catch (PlaywrightException)
        {
            return await ContainsIdentityProviderMarkerAsync();
        }
    }

    /// <summary>Clicks "¿No tienes cuenta? Regístrate" and waits for the Register form.</summary>
    public async Task<RegisterPage> ClickRegisterLinkAsync()
    {
        await ClickAsync(ByPartialText(RegisterLinkText));
        return await RegisterPage.CreateAsync(Page);
    }

    // ── Internals ────────────────────────────────────────────────────────

    private ILocator EmailInput() => ByPlaceholder(EmailPlaceholder);
    private ILocator PasswordInput() => ByPlaceholder(PasswordPlaceholder);
    private ILocator GoogleButton() => ByPartialText(GoogleText);
    private ILocator SubmitButton() => InteractiveWithText(SubmitText);

    private static string KeywordsJsArray(IEnumerable<string> keywords) =>
        "[" + string.Join(',', keywords.Select(k => $"'{k}'")) + "]";

    private static string LoginSettledPredicate() =>
        "() => {"
        + "const text = document.body.innerText;"
        + "const home = text.includes('Bienvenido');"
        + "const lower = text.toLowerCase();"
        + $"const feedback = {KeywordsJsArray(FeedbackKeywords)}.some(k => lower.includes(k));"
        + "const invalid = Array.from(document.querySelectorAll('input'))"
        + ".some(el => el.required && !el.checkValidity());"
        + "return home || feedback || invalid;"
        + "}";

    private async Task<bool> ContainsIdentityProviderMarkerAsync()
    {
        var url = Page.Url.ToLowerInvariant();
        var body = (await Page.EvaluateAsync<string>("() => document.body.innerText")).ToLowerInvariant();
        return url.Contains("google") || url.Contains("firebase") || url.Contains("identitytoolkit")
               || body.Contains("google") || body.Contains("firebase");
    }
}
