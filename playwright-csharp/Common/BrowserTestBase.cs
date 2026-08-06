using System.Text;
using System.Text.Json;
using Microsoft.Playwright;
using Microsoft.Playwright.NUnit;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Base class for the ClimaNuvem browser system tests. Mirrors
/// selenium-java's <c>BaseLoggedClass</c>, built on top of
/// <see cref="PageTest"/> — Playwright's own NUnit integration already
/// gives every test a fresh, isolated <see cref="PageTest.Page"/> (backed
/// by a fresh <see cref="IBrowserContext"/>) with no manual lifecycle code
/// needed, the direct equivalent of Selenium's fresh-ChromeDriver-per-test
/// plus <c>--incognito</c>.
///
/// Entry points for test methods:
///   <see cref="OnWelcomePageAsync"/> — navigates to the frontend root and
///     returns a <see cref="WelcomePage"/>, which waits internally until
///     the page is ready.
///   <see cref="LoginAsGuestAsync"/> — convenience shortcut that clicks
///     "Continuar como invitado" and returns a <see cref="HomePage"/>.
///
/// Set <c>CI=true</c> for headless Chromium in CI (see
/// <see cref="LaunchOptionsAsync"/>).
/// </summary>
public abstract class BrowserTestBase : PageTest
{
    protected static string FrontendUrl => TestSettings.FrontendUrl;

    private static TestAccounts? _testAccounts;

    protected static TestAccounts TestAccountsData => _testAccounts ??= LoadAccounts();

    public override async Task<BrowserTypeLaunchOptions?> LaunchOptionsAsync()
    {
        var options = await base.LaunchOptionsAsync() ?? new BrowserTypeLaunchOptions();
        options.Headless = TestSettings.Ci;
        options.Args = ["--disable-blink-features=AutomationControlled"];
        return options;
    }

    protected async Task<WelcomePage> OnWelcomePageAsync()
    {
        await Page.GotoAsync(FrontendUrl);
        return await WelcomePage.CreateAsync(Page);
    }

    /// <summary>
    /// Clicks "Continuar como invitado", which triggers Firebase anonymous
    /// auth, and waits for the Home screen to mount.
    /// </summary>
    protected async Task<HomePage> LoginAsGuestAsync()
    {
        var welcome = await OnWelcomePageAsync();
        return await welcome.ClickAnonymousLoginAsync();
    }

    protected async Task<HomePage> LoginAsProfileUserAsync()
    {
        var account = TestAccountsData.ProfileAccount();
        var welcome = await OnWelcomePageAsync();
        var login = await welcome.ClickLoginButtonAsync();
        await login.LoginAsync(account.Email, account.Password);
        return await login.WaitForHomeAsync();
    }

    /// <summary>
    /// Best-effort cleanup for the unique account RegisterSystemTests
    /// creates. No-ops (with a log line) when FIREBASE_WEB_API_KEY is not
    /// configured.
    /// </summary>
    protected static async Task DeleteFirebaseAccountIfConfiguredAsync(string email, string password)
    {
        var apiKey = TestSettings.FirebaseWebApiKey;
        if (string.IsNullOrEmpty(apiKey))
        {
            TestContext.Progress.WriteLine($"Skipping Firebase account cleanup for {email}: FIREBASE_WEB_API_KEY not configured");
            return;
        }

        using var client = new HttpClient();
        try
        {
            var signInPayload = JsonSerializer.Serialize(new { email, password, returnSecureToken = true });
            using var signInResponse = await client.PostAsync(
                $"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={apiKey}",
                new StringContent(signInPayload, Encoding.UTF8, "application/json"));
            signInResponse.EnsureSuccessStatusCode();
            var signInBody = JsonDocument.Parse(await signInResponse.Content.ReadAsStringAsync()).RootElement;
            var idToken = signInBody.GetProperty("idToken").GetString();

            var deletePayload = JsonSerializer.Serialize(new { idToken });
            using var deleteResponse = await client.PostAsync(
                $"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={apiKey}",
                new StringContent(deletePayload, Encoding.UTF8, "application/json"));
            deleteResponse.EnsureSuccessStatusCode();
            TestContext.Progress.WriteLine($"Deleted Firebase account created during test: {email}");
        }
        catch (Exception ex)
        {
            TestContext.Progress.WriteLine($"Could not delete Firebase account created during test: {email} ({ex.Message})");
        }
    }

    private static TestAccounts LoadAccounts()
    {
        try
        {
            return TestAccounts.Load(TestSettings.AccountsFile);
        }
        catch (Exception ex)
        {
            TestContext.Progress.WriteLine(
                $"Could not load system-test accounts from {TestSettings.AccountsFile} ({ex.Message}). "
                + "Tests that require accounts will fail only when they request one.");
            return TestAccounts.Empty();
        }
    }
}
