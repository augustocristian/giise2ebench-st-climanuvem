using PlaywrightStClimanuvem.Common;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Tests.E2e;

/// <summary>
/// Browser system tests for the login functionality, derived from the
/// same Base Choice table as selenium-java's <c>TestLoginSystem</c>.
/// <c>[TestCaseSource]</c> is NUnit's direct equivalent of JUnit's
/// <c>@ParameterizedTest</c>/<c>@MethodSource</c> — each account row
/// becomes its own test instance with its own fresh browser context,
/// courtesy of <see cref="BrowserTestBase"/>'s <c>PageTest</c> base.
/// </summary>
[TestFixture]
public class LoginSystemTests : BrowserTestBase
{
    private static IEnumerable<TestAccount> LoginAccountsSource() => TestAccountsData.LoginAccounts();

    [Test]
    [Description("BASE - Guest login reaches Home")]
    public async Task GuestLoginReachesHome()
    {
        var home = await LoginAsGuestAsync();
        Assert.That(await home.IsWelcomeMessageVisibleAsync(), Is.True, "Guest login must reach the Home screen");
    }

    [Test]
    [Description("BASE - Google login provider flow is available")]
    public async Task GoogleLoginProviderFlowIsAvailable()
    {
        var welcome = await OnWelcomePageAsync();
        var login = await welcome.ClickLoginButtonAsync();

        Assert.Multiple(async () =>
        {
            Assert.That(await login.IsGoogleLoginPresentAsync(), Is.True, "Google login option must be available");
            Assert.That(
                await login.ClickGoogleLoginStartsProviderAsync(), Is.True,
                "Clicking Google login must start the provider flow");
        });
    }

    [TestCaseSource(nameof(LoginAccountsSource))]
    [Description("2 - Existing email with correct password reaches Home")]
    public async Task ExistingEmailWithCorrectPasswordReachesHome(TestAccount account)
    {
        var welcome = await OnWelcomePageAsync();
        var login = await welcome.ClickLoginButtonAsync();
        await login.LoginAsync(account.Email, account.Password);
        var home = await login.WaitForHomeAsync();

        Assert.That(
            await home.IsWelcomeMessageVisibleAsync(), Is.True,
            "Existing email with correct password must reach the Home screen");
    }

    [TestCaseSource(nameof(LoginAccountsSource))]
    [Description("3 - Invalid email/password login attempts are rejected")]
    public async Task InvalidEmailPasswordLoginAttemptsAreRejected(TestAccount account)
    {
        var unknown = TestAccountsData.UnknownAccount();
        var welcome = await OnWelcomePageAsync();
        var login = await welcome.ClickLoginButtonAsync();

        Assert.Multiple(async () =>
        {
            await AssertLoginRejectedAsync(
                login, account.Email, "",
                "Existing email with empty password must remain on Login and show validation or an error");
            await AssertLoginRejectedAsync(
                login, unknown.Email, unknown.Password,
                "Unknown email with empty password must remain on Login and show validation or an error");
            await AssertLoginRejectedAsync(login, "", "", "Empty credentials must remain on Login and show validation");
            await AssertLoginRejectedAsync(
                login, account.Email, unknown.Password,
                "Existing email with incorrect password must remain on Login and show an error");
        });
    }

    private static async Task AssertLoginRejectedAsync(LoginPage login, string email, string password, string message)
    {
        await login.LoginAsync(email, password);
        try
        {
            await login.WaitForLoginFailureAsync();
            Assert.That(await login.HasLoginErrorOrValidationAsync(), Is.True, message);
        }
        finally
        {
            await login.CloseLoginFeedbackIfPresentAsync();
        }
    }
}
