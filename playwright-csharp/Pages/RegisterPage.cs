using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Page Object for the Register form. <see cref="CreateAsync"/> waits
/// until the username input is visible. Mirrors selenium-java's
/// <c>RegisterPage</c>.
/// </summary>
public sealed class RegisterPage : BasePage
{
    private static readonly string[] RegisterFeedbackKeywords =
    [
        "error", "inválid", "invalid", "contraseña", "correo", "usuario", "coincid", "uso", "obligatorio", "requerid",
    ];

    private static readonly string[] VerifyDialogKeywords = ["verific", "correo"];

    private const string UsernamePlaceholder = "Nombre de usuario";
    private const string EmailPlaceholder = "Correo electrónico";
    private const string PasswordPlaceholder = "Contraseña";
    private const string ConfirmPasswordPlaceholder = "Confirmar contraseña";
    private const string LoginLinkText = "Inicia sesión";
    private const string HomeMarkerText = "Bienvenido";

    private RegisterPage(IPage page) : base(page)
    {
    }

    public static async Task<RegisterPage> CreateAsync(IPage page)
    {
        var registerPage = new RegisterPage(page);
        await WaitForAsync(registerPage.UsernameInput());
        return registerPage;
    }

    // ── Queries ──────────────────────────────────────────────────────────

    public Task<bool> IsUsernameInputPresentAsync() => IsPresentAsync(UsernameInput());
    public Task<bool> IsEmailInputPresentAsync() => IsPresentAsync(ByPlaceholder(EmailPlaceholder));
    public Task<bool> IsPasswordInputPresentAsync() => IsPresentAsync(ByPlaceholder(PasswordPlaceholder));
    public Task<bool> IsConfirmPasswordInputPresentAsync() => IsPresentAsync(ByPlaceholder(ConfirmPasswordPlaceholder));
    public Task<bool> IsLoginLinkPresentAsync() => IsPresentAsync(ByPartialText(LoginLinkText));
    public Task<bool> IsHomeVisibleAsync() => IsPresentAsync(ByPartialText(HomeMarkerText));

    public async Task<bool> IsVerificationDialogVisibleAsync() =>
        await BodyTextContainsAllAsync(VerifyDialogKeywords);

    public async Task<bool> HasRegisterErrorOrValidationAsync() =>
        await BodyTextContainsAnyAsync(RegisterFeedbackKeywords) || await HasInvalidRequiredInputAsync();

    // ── Actions ──────────────────────────────────────────────────────────

    public async Task<RegisterPage> EnterUsernameAsync(string username)
    {
        await FillAsync(UsernameInput(), username);
        return this;
    }

    public async Task<RegisterPage> EnterEmailAsync(string email)
    {
        await FillAsync(ByPlaceholder(EmailPlaceholder), email);
        return this;
    }

    public async Task<RegisterPage> EnterPasswordAsync(string password)
    {
        await FillAsync(ByPlaceholder(PasswordPlaceholder), password);
        return this;
    }

    public async Task<RegisterPage> EnterConfirmPasswordAsync(string password)
    {
        await FillAsync(ByPlaceholder(ConfirmPasswordPlaceholder), password);
        return this;
    }

    public async Task<RegisterPage> SubmitRegisterAsync()
    {
        await ClickLastVisibleAsync(InteractiveWithAnyText("registr", "crear"));
        return this;
    }

    public async Task<RegisterPage> RegisterAsync(string username, string email, string password, string confirmPassword)
    {
        await EnterUsernameAsync(username);
        await EnterEmailAsync(email);
        await EnterPasswordAsync(password);
        await EnterConfirmPasswordAsync(confirmPassword);
        return await SubmitRegisterAsync();
    }

    public async Task<HomePage> WaitForHomeAsync()
    {
        await WaitForAsync(ByPartialText(HomeMarkerText));
        return await HomePage.CreateAsync(Page);
    }

    public async Task<RegisterPage> WaitForVerificationDialogAsync()
    {
        const string predicate =
            "() => {"
            + "const lower = document.body.innerText.toLowerCase();"
            + "return lower.includes('verific') && lower.includes('correo');"
            + "}";
        await WaitUntilAsync(predicate);
        return this;
    }

    public async Task<RegisterPage> WaitForRegisterFailureAsync()
    {
        var predicate =
            "() => {"
            + "const lower = document.body.innerText.toLowerCase();"
            + $"const feedback = {KeywordsJsArray(RegisterFeedbackKeywords)}.some(k => lower.includes(k));"
            + "const invalid = Array.from(document.querySelectorAll('input'))"
            + ".some(el => el.required && !el.checkValidity());"
            + $"const usernamePresent = !!document.querySelector('input[placeholder=\"{UsernamePlaceholder}\"]');"
            + "return (feedback || invalid) && usernamePresent;"
            + "}";
        await WaitUntilAsync(predicate);
        return this;
    }

    /// <summary>Navigates back to the Login form.</summary>
    public async Task<LoginPage> ClickLoginLinkAsync()
    {
        await ClickAsync(ByPartialText(LoginLinkText));
        return await LoginPage.CreateAsync(Page);
    }

    // ── Internals ────────────────────────────────────────────────────────

    private ILocator UsernameInput() => ByPlaceholder(UsernamePlaceholder);

    private async Task<bool> BodyTextContainsAllAsync(IEnumerable<string> keywords)
    {
        var text = (await Page.EvaluateAsync<string>("() => document.body.innerText")).ToLowerInvariant();
        return keywords.All(keyword => text.Contains(keyword.ToLowerInvariant()));
    }

    private static string KeywordsJsArray(IEnumerable<string> keywords) =>
        "[" + string.Join(',', keywords.Select(k => $"'{k}'")) + "]";
}
