using System.Text.RegularExpressions;
using PlaywrightStClimanuvem.Common;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Tests.E2e;

/// <summary>
/// Browser system tests for account creation, derived from the same Base
/// Choice table as selenium-java's <c>TestRegisterSystem</c>.
/// </summary>
[TestFixture]
public class RegisterSystemTests : BrowserTestBase
{
    private const string ValidUsername20 = "TestUser123456789012";
    private const string Username2 = "ab";
    private const string Username21 = "TestUser1234567890123";
    private const string ValidPassword = "Test12";
    private const string Password5 = "Test1";
    private const string PasswordNoUppercase = "test12";
    private const string PasswordNoNumber = "Testaa";
    private const string DifferentConfirmPassword = "Other1";

    private const string ErrorTitle = "Error";
    private const string UsernameLengthMessage = "Username must be between 3 and 20 characters.";
    private const string InvalidEmailMessage = "Please enter a valid email address.";
    private const string PasswordLengthMessage = "Password must be at least 6 characters.";
    private const string PasswordsDoNotMatchMessage = "Passwords do not match.";
    private const string EmailInUseMessage = "This email is already in use by another account.";
    private static readonly Regex WeakPasswordMessage = new("uppercase letter and one number|too weak");

    [Test]
    [Description("BASE - Valid account data creates the account")]
    public async Task ValidAccountDataCreatesAccount()
    {
        var email = UniqueRegisterEmail();

        try
        {
            var registerPage = await OpenRegisterPageAsync();
            await registerPage.RegisterAsync(ValidUsername20, email, ValidPassword, ValidPassword);

            await registerPage.ExpectFeedbackAsync("Successful registration", "verification email");
        }
        finally
        {
            await DeleteFirebaseAccountIfConfiguredAsync(email, ValidPassword);
        }
    }

    [Test]
    [Description("2 - Username and email validation errors are rejected")]
    public async Task UsernameAndEmailValidationErrorsAreRejected()
    {
        var existingAccount = TestAccountsData.LoginAccount();

        await AssertRegistrationRejectedAsync("", UniqueRegisterEmail(), ValidPassword, ValidPassword, UsernameLengthMessage);
        await AssertRegistrationRejectedAsync(Username2, UniqueRegisterEmail(), ValidPassword, ValidPassword, UsernameLengthMessage);
        await AssertRegistrationRejectedAsync(ValidUsername20, "invalid-email", ValidPassword, ValidPassword, InvalidEmailMessage);
        await AssertRegistrationRejectedAsync(ValidUsername20, existingAccount.Email, ValidPassword, ValidPassword, EmailInUseMessage);
    }

    [Test]
    [Description("3 - Password and confirmation validation errors are rejected")]
    public async Task PasswordAndConfirmationValidationErrorsAreRejected()
    {
        await AssertRegistrationRejectedAsync(ValidUsername20, UniqueRegisterEmail(), "", "", PasswordLengthMessage);
        await AssertRegistrationRejectedAsync(ValidUsername20, UniqueRegisterEmail(), Password5, Password5, PasswordLengthMessage);
        await AssertRegistrationRejectedAsync(
            ValidUsername20, UniqueRegisterEmail(), ValidPassword, DifferentConfirmPassword, PasswordsDoNotMatchMessage);
    }

    [Test]
    [Description("2b - The username field caps its value at 20 characters")]
    public async Task UsernameFieldCapsLengthAtTwentyCharacters()
    {
        var registerPage = await OpenRegisterPageAsync();
        await registerPage.ExpectUsernameValueAfterTypingAsync(Username21, ValidUsername20);
    }

    [Test]
    [Description("3b - Passwords without an uppercase letter or a number are rejected")]
    public async Task PasswordPolicyViolationsAreRejected()
    {
        Assume.That(TestSettings.PasswordPolicyEnforced,
            "The Firebase Auth emulator does not enforce password policies; set PASSWORD_POLICY_ENFORCED=true against a real project.");

        await AssertRegistrationRejectedAsync(
            ValidUsername20, UniqueRegisterEmail(), PasswordNoUppercase, PasswordNoUppercase, WeakPasswordMessage);
        await AssertRegistrationRejectedAsync(
            ValidUsername20, UniqueRegisterEmail(), PasswordNoNumber, PasswordNoNumber, WeakPasswordMessage);
    }

    private async Task<RegisterPage> OpenRegisterPageAsync() =>
        await (await OpenLoginPageAsync()).OpenRegisterAsync();

    private Task AssertRegistrationRejectedAsync(
        string username, string email, string password, string confirmPassword, string expectedMessage) =>
        AssertRegistrationRejectedAsync(
            username, email, password, confirmPassword, new Regex(Regex.Escape(expectedMessage)));

    private async Task AssertRegistrationRejectedAsync(
        string username, string email, string password, string confirmPassword, Regex expectedMessage)
    {
        var registerPage = await OpenRegisterPageAsync();
        await registerPage.RegisterAsync(username, email, password, confirmPassword);
        await registerPage.ExpectFeedbackAsync(ErrorTitle, expectedMessage);
    }

    private static string UniqueRegisterEmail() =>
        $"climanuvem.test+{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}@{TestSettings.RegisterEmailDomain}";
}
