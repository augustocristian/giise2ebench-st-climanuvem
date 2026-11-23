using Microsoft.Playwright;
using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>Welcome (root) screen, the first page any visitor sees.</summary>
public sealed class WelcomePage(IPage page) : BasePage(page)
{
    protected override Task ExpectReadyAsync() => ExpectVisibleAsync(TestIds.Welcome.GuestButton);

    public async Task<LoginPage> OpenLoginAsync()
    {
        await ClickAsync(TestIds.Welcome.LoginButton);
        return await WhenReadyAsync(new LoginPage(Page));
    }

    /// <summary>Continues as guest (Firebase anonymous auth) and waits for Home.</summary>
    public async Task<HomePage> ContinueAsGuestAsync()
    {
        await ClickAsync(TestIds.Welcome.GuestButton);
        return await WhenReadyAsync(new HomePage(Page));
    }
}
