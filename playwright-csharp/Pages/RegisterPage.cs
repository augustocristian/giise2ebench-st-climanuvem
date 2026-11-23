using Microsoft.Playwright;
using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>Register form.</summary>
public sealed class RegisterPage(IPage page) : BasePage(page)
{
    protected override string FeedbackTestId => TestIds.Register.Feedback;

    protected override Task ExpectReadyAsync() => ExpectVisibleAsync(TestIds.Register.UsernameInput);

    /// <summary>Types into the username field and asserts the stored value, which the input caps at its max length.</summary>
    public async Task ExpectUsernameValueAfterTypingAsync(string typed, string expected)
    {
        await FillAsync(TestIds.Register.UsernameInput, typed);
        await ExpectValueAsync(TestIds.Register.UsernameInput, expected);
    }

    /// <summary>Fills the whole form and submits it without waiting for a result.</summary>
    public async Task RegisterAsync(string username, string email, string password, string confirmPassword)
    {
        await FillAsync(TestIds.Register.UsernameInput, username);
        await FillAsync(TestIds.Register.EmailInput, email);
        await FillAsync(TestIds.Register.PasswordInput, password);
        await FillAsync(TestIds.Register.ConfirmPasswordInput, confirmPassword);
        await ClickAsync(TestIds.Register.SubmitButton);
    }
}
