using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Page Object for the Welcome (root) screen — the first page any visitor
/// sees. <see cref="CreateAsync"/> waits until the guest-login button is
/// visible, guaranteeing the app has fully mounted before any assertion
/// runs. Mirrors selenium-java's <c>WelcomePage</c>.
/// </summary>
public sealed class WelcomePage : BasePage
{
    private const string GuestButtonText = "Continuar como invitado";
    private const string LoginButtonText = "Iniciar Sesión";
    private const string AppTitleText = "ClimaNuvem";
    private const string TaglineText = "Meteorólogo de bolsillo";

    private WelcomePage(IPage page) : base(page)
    {
    }

    public static async Task<WelcomePage> CreateAsync(IPage page)
    {
        var welcomePage = new WelcomePage(page);
        await WaitForAsync(welcomePage.GuestButton());
        return welcomePage;
    }

    // ── Queries ──────────────────────────────────────────────────────────

    public Task<bool> IsAppTitleVisibleAsync() => IsPresentAsync(ByPartialText(AppTitleText));
    public Task<bool> IsTaglineVisibleAsync() => IsPresentAsync(ByPartialText(TaglineText));
    public Task<bool> IsLoginButtonPresentAsync() => IsPresentAsync(LoginButton());
    public Task<bool> IsGuestButtonPresentAsync() => IsPresentAsync(GuestButton());
    public Task<bool> IsHomeVisibleAsync() => IsPresentAsync(ByPartialText("Bienvenido"));

    // ── Actions ──────────────────────────────────────────────────────────

    /// <summary>Clicks "Iniciar Sesión" and waits for the Login form to appear.</summary>
    public async Task<LoginPage> ClickLoginButtonAsync()
    {
        await ClickAsync(LoginButton());
        return await LoginPage.CreateAsync(Page);
    }

    /// <summary>
    /// Clicks "Continuar como invitado", which triggers Firebase anonymous
    /// auth, and waits for the Home screen to mount.
    /// </summary>
    public async Task<HomePage> ClickAnonymousLoginAsync()
    {
        await ClickAsync(GuestButton());
        return await HomePage.CreateAsync(Page);
    }

    private ILocator GuestButton() => ByPartialText(GuestButtonText);
    private ILocator LoginButton() => ByPartialText(LoginButtonText);
}
