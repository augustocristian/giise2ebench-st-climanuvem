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
    private const string ValidUsername20 = "usuarioPrueba1234567";
    private const string Username2 = "ab";
    private const string Username21 = "usuarioPrueba12345678";
    private const string ValidPassword = "Test12";
    private const string Password5 = "Test1";
    private const string PasswordNoUppercase = "test12";
    private const string PasswordNoNumber = "Testaa";
    private const string DifferentConfirmPassword = "Other1";

    [Test]
    [Description("BASE - Valid account data creates the account")]
    public async Task ValidAccountDataCreatesAccount()
    {
        var email = UniqueRegisterEmail();

        try
        {
            var registerPage = await OpenRegisterPageAsync();
            await registerPage.RegisterAsync(ValidUsername20, email, ValidPassword, ValidPassword);
            await registerPage.WaitForVerificationDialogAsync();

            Assert.That(
                await registerPage.IsVerificationDialogVisibleAsync(), Is.True,
                "Valid registration data must create the account and show email-verification guidance");
        }
        finally
        {
            await DeleteFirebaseAccountIfConfiguredAsync(email, ValidPassword);
        }
    }

    [Test]
    [Description("2 - Username and email validation errors are rejected")]
    public void UsernameAndEmailValidationErrorsAreRejected()
    {
        var existingAccount = TestAccountsData.LoginAccount();

        Assert.Multiple(async () =>
        {
            await AssertRegistrationRejectedAsync(
                "", UniqueRegisterEmail(), ValidPassword, ValidPassword, "Empty username must be rejected");
            await AssertRegistrationRejectedAsync(
                Username2, UniqueRegisterEmail(), ValidPassword, ValidPassword, "Two-character username must be rejected");
            await AssertRegistrationRejectedAsync(
                Username21, UniqueRegisterEmail(), ValidPassword, ValidPassword,
                "Twenty-one-character username must be rejected");
            await AssertRegistrationRejectedAsync(
                ValidUsername20, "correo-invalido", ValidPassword, ValidPassword, "Invalid email must be rejected");
            await AssertRegistrationRejectedAsync(
                ValidUsername20, existingAccount.Email, ValidPassword, ValidPassword,
                "Email already in use must be rejected");
        });
    }

    [Test]
    [Description("3 - Password and confirmation validation errors are rejected")]
    public void PasswordAndConfirmationValidationErrorsAreRejected()
    {
        Assert.Multiple(async () =>
        {
            await AssertRegistrationRejectedAsync(
                ValidUsername20, UniqueRegisterEmail(), "", "", "Empty password must be rejected");
            await AssertRegistrationRejectedAsync(
                ValidUsername20, UniqueRegisterEmail(), Password5, Password5, "Five-character password must be rejected");
            await AssertRegistrationRejectedAsync(
                ValidUsername20, UniqueRegisterEmail(), PasswordNoUppercase, PasswordNoUppercase,
                "Password without uppercase letters must be rejected");
            await AssertRegistrationRejectedAsync(
                ValidUsername20, UniqueRegisterEmail(), PasswordNoNumber, PasswordNoNumber,
                "Password without numbers must be rejected");
            await AssertRegistrationRejectedAsync(
                ValidUsername20, UniqueRegisterEmail(), ValidPassword, DifferentConfirmPassword,
                "Non-matching password confirmation must be rejected");
        });
    }

    private async Task<RegisterPage> OpenRegisterPageAsync()
    {
        var welcome = await OnWelcomePageAsync();
        var login = await welcome.ClickLoginButtonAsync();
        return await login.ClickRegisterLinkAsync();
    }

    private async Task AssertRegistrationRejectedAsync(
        string username, string email, string password, string confirmPassword, string message)
    {
        var registerPage = await OpenRegisterPageAsync();
        await registerPage.RegisterAsync(username, email, password, confirmPassword);
        await registerPage.WaitForRegisterFailureAsync();
        Assert.That(await registerPage.HasRegisterErrorOrValidationAsync(), Is.True, message);
    }

    private static string UniqueRegisterEmail() =>
        $"climanuvem.test+{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}@{TestSettings.RegisterEmailDomain}";
}
