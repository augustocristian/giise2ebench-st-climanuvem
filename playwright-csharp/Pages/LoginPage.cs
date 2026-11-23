using Microsoft.Playwright;
using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>Login form.</summary>
public sealed class LoginPage(IPage page) : BasePage(page)
{
    private const int PopupTimeoutMs = 5_000;

    protected override string FeedbackTestId => TestIds.Login.Feedback;

    protected override Task ExpectReadyAsync() => ExpectVisibleAsync(TestIds.Login.EmailInput);

    public Task ExpectGoogleButtonVisibleAsync() => ExpectVisibleAsync(TestIds.Login.GoogleButton);

    /// <summary>Fills both fields and submits the form without waiting for a result.</summary>
    public async Task SubmitCredentialsAsync(string email, string password)
    {
        await FillAsync(TestIds.Login.EmailInput, email);
        await FillAsync(TestIds.Login.PasswordInput, password);
        await ClickAsync(TestIds.Login.SubmitButton);
    }

    /// <summary>Logs in with valid credentials and waits for Home.</summary>
    public async Task<HomePage> LoginAsync(string email, string password)
    {
        await SubmitCredentialsAsync(email, password);
        return await WhenReadyAsync(new HomePage(Page));
    }

    public async Task<RegisterPage> OpenRegisterAsync()
    {
        await ClickAsync(TestIds.Login.RegisterLink);
        return await WhenReadyAsync(new RegisterPage(Page));
    }

    /// <summary>
    /// Clicks "Continue with Google". The provider flow counts as started when a
    /// popup opens or the page reports a Google-specific dialog or identity URL.
    /// </summary>
    public async Task<bool> StartGoogleLoginAsync()
    {
        try
        {
            await Page.RunAndWaitForPopupAsync(
                () => ClickAsync(TestIds.Login.GoogleButton),
                new PageRunAndWaitForPopupOptions { Timeout = PopupTimeoutMs });
            return true;
        }
        catch (TimeoutException)
        {
            var url = Page.Url;
            return url.Contains("google", StringComparison.OrdinalIgnoreCase)
                   || url.Contains("firebase", StringComparison.OrdinalIgnoreCase)
                   || await ByTestId(FeedbackTestId).Filter(new LocatorFilterOptions { HasText = "Google" }).IsVisibleAsync();
        }
    }
}
