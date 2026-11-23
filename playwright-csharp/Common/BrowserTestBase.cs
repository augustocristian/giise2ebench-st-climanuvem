using System.Text;
using System.Text.Json;
using Microsoft.Playwright;
using Microsoft.Playwright.NUnit;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Base class for the ClimaNuvem browser system tests, built on
/// <see cref="PageTest"/>: every test gets a fresh, isolated
/// <see cref="PageTest.Page"/> backed by its own browser context.
/// Hosts the single timeout configuration and the flows shared by several
/// test classes (open Welcome, log in, open a profile). Set <c>CI=true</c>
/// for headless Chromium (see <see cref="LaunchOptionsAsync"/>).
/// </summary>
public abstract class BrowserTestBase : PageTest
{
    /// <summary>Single timeout for actions, navigation and web-first assertions.</summary>
    private const float DefaultTimeoutMs = 30_000;

    private static TestAccounts? _testAccounts;

    protected static TestAccounts TestAccountsData => _testAccounts ??= LoadAccounts();

    public override async Task<BrowserTypeLaunchOptions?> LaunchOptionsAsync()
    {
        var options = await base.LaunchOptionsAsync() ?? new BrowserTypeLaunchOptions();
        options.Headless = TestSettings.Ci;
        options.Args = ["--disable-blink-features=AutomationControlled"];
        return options;
    }

    [OneTimeSetUp]
    public void ConfigureExpectTimeout() => Assertions.SetDefaultExpectTimeout(DefaultTimeoutMs);

    [SetUp]
    public void ConfigureActionTimeout() => Context.SetDefaultTimeout(DefaultTimeoutMs);

    protected async Task<WelcomePage> OpenWelcomePageAsync()
    {
        await Page.GotoAsync(TestSettings.FrontendUrl);
        return await BasePage.WhenReadyAsync(new WelcomePage(Page));
    }

    protected async Task<LoginPage> OpenLoginPageAsync() =>
        await (await OpenWelcomePageAsync()).OpenLoginAsync();

    protected async Task<HomePage> LoginAsGuestAsync() =>
        await (await OpenWelcomePageAsync()).ContinueAsGuestAsync();

    protected async Task<HomePage> LoginAsync(TestAccount account) =>
        await (await OpenLoginPageAsync()).LoginAsync(account.Email, account.Password);

    protected async Task<ProfilePage> OpenGuestProfileAsync()
    {
        var profile = await (await LoginAsGuestAsync()).OpenProfileAsync();
        await profile.ExpectGuestViewAsync();
        return profile;
    }

    protected async Task<ProfilePage> OpenAuthenticatedProfileAsync(TestAccount account)
    {
        var profile = await (await LoginAsync(account)).OpenProfileAsync();
        await profile.ExpectAuthenticatedViewAsync();
        return profile;
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
