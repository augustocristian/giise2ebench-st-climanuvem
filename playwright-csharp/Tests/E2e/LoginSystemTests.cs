using System.Text.RegularExpressions;
using PlaywrightStClimanuvem.Common;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Tests.E2e;

/// <summary>
/// Browser system tests for the login functionality, derived from the
/// same Base Choice table as selenium-java's <c>TestLoginSystem</c>.
/// Each account row becomes its own test instance with a fresh browser context.
/// </summary>
[TestFixture]
public class LoginSystemTests : BrowserTestBase
{
    private const string ErrorTitle = "Error";
    private const string InvalidEmailMessage = "Please enter a valid email address.";
    /// <summary>Real Firebase answers with a generic message; the emulator is more specific (wrong password / unknown email).</summary>
    private static readonly Regex BadCredentialsMessage = new("Incorrect credentials|password is incorrect|No account exists|Authentication error");

    private static IEnumerable<TestAccount> LoginAccountsSource() => TestAccountsData.LoginAccounts();

    [Test]
    [Description("BASE - Guest login reaches Home")]
    public async Task GuestLoginReachesHome()
    {
        var home = await LoginAsGuestAsync();
        await home.ExpectWelcomeVisibleAsync();
    }

    [Test]
    [Description("BASE - Google login provider flow is available")]
    public async Task GoogleLoginProviderFlowIsAvailable()
    {
        var login = await OpenLoginPageAsync();
        await login.ExpectGoogleButtonVisibleAsync();

        Assert.That(await login.StartGoogleLoginAsync(), Is.True, "Clicking Google login must start the provider flow");
    }

    [TestCaseSource(nameof(LoginAccountsSource))]
    [Description("2 - Existing email with correct password reaches Home")]
    public async Task ExistingEmailWithCorrectPasswordReachesHome(TestAccount account)
    {
        var home = await LoginAsync(account);
        await home.ExpectWelcomeVisibleAsync();
    }

    [TestCaseSource(nameof(LoginAccountsSource))]
    [Description("3 - Invalid email/password login attempts are rejected")]
    public async Task InvalidEmailPasswordLoginAttemptsAreRejected(TestAccount account)
    {
        var unknown = TestAccountsData.UnknownAccount();
        var login = await OpenLoginPageAsync();

        // Existing email with empty password
        await AssertRejectedAsync(login, account.Email, "", BadCredentialsMessage);
        // Unknown email
        await AssertRejectedAsync(login, unknown.Email, unknown.Password, BadCredentialsMessage);
        // Empty credentials
        await AssertRejectedAsync(login, "", "", InvalidEmailMessage);
        // Existing email with incorrect password
        await AssertRejectedAsync(login, account.Email, unknown.Password, BadCredentialsMessage);
    }

    private static async Task AssertRejectedAsync(LoginPage login, string email, string password, Regex expectedMessage)
    {
        await login.SubmitCredentialsAsync(email, password);
        await login.ExpectFeedbackAsync(ErrorTitle, expectedMessage);
        await login.DismissFeedbackAsync();
    }

    private static Task AssertRejectedAsync(LoginPage login, string email, string password, string expectedMessage) =>
        AssertRejectedAsync(login, email, password, new Regex(Regex.Escape(expectedMessage)));
}
