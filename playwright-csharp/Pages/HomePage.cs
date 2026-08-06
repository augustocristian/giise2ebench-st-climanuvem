using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Page Object for the Home screen — shown after a successful login.
/// <see cref="CreateAsync"/> waits until both the welcome message and the
/// "Analizar Imagen" quick-action card are visible. Mirrors
/// selenium-java's <c>HomePage</c>.
/// </summary>
public sealed class HomePage : BasePage
{
    private const string WelcomeMessageText = "Bienvenido";
    private const string AnalyzeCardText = "Analizar Imagen";
    private const string HistoryCardText = "Historial";
    private const string LogoutCardText = "Cerrar Sesión";

    private HomePage(IPage page) : base(page)
    {
    }

    public static async Task<HomePage> CreateAsync(IPage page)
    {
        var homePage = new HomePage(page);
        await WaitForAsync(homePage.WelcomeMessage());
        await WaitForAsync(homePage.AnalyzeCard());
        return homePage;
    }

    // ── Queries ──────────────────────────────────────────────────────────

    public Task<bool> IsWelcomeMessageVisibleAsync() => IsPresentAsync(WelcomeMessage());
    public Task<bool> IsAnalyzeCardVisibleAsync() => IsPresentAsync(AnalyzeCard());
    public Task<bool> IsHistoryCardVisibleAsync() => IsPresentAsync(ByPartialText(HistoryCardText));
    public Task<bool> IsLogoutCardVisibleAsync() => IsPresentAsync(ByPartialText(LogoutCardText));

    // ── Actions ──────────────────────────────────────────────────────────

    /// <summary>Navigates to the Capture screen.</summary>
    public async Task<CapturePage> ClickAnalyzeImageAsync()
    {
        await ClickAsync(AnalyzeCard());
        return await CapturePage.CreateAsync(Page);
    }

    /// <summary>Opens Profile through the router URL, avoiding flaky React Native Web card clicks.</summary>
    public async Task<ProfilePage> ClickProfileAsync()
    {
        var origin = await Page.EvaluateAsync<string>("() => window.location.origin");
        await Page.GotoAsync($"{origin}/profile");
        return await ProfilePage.CreateAsync(Page);
    }

    /// <summary>Clicks "Cerrar Sesión" and waits for the Welcome screen to re-appear.</summary>
    public async Task<WelcomePage> ClickLogoutAsync()
    {
        await ClickAsync(ByPartialText(LogoutCardText));
        return await WelcomePage.CreateAsync(Page);
    }

    private ILocator WelcomeMessage() => ByPartialText(WelcomeMessageText);
    private ILocator AnalyzeCard() => ByPartialText(AnalyzeCardText);
}
