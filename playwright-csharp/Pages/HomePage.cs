using Microsoft.Playwright;
using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>Home screen, shown after a successful login.</summary>
public sealed class HomePage(IPage page) : BasePage(page)
{
    protected override async Task ExpectReadyAsync()
    {
        await ExpectVisibleAsync(TestIds.Home.Welcome);
        await ExpectVisibleAsync(TestIds.Home.AnalyzeCard);
    }

    public Task ExpectWelcomeVisibleAsync() => ExpectVisibleAsync(TestIds.Home.Welcome);

    /// <summary>Opens Profile through the welcome banner, which navigates there.</summary>
    public async Task<ProfilePage> OpenProfileAsync()
    {
        await ClickAsync(TestIds.Home.Welcome);
        return await WhenReadyAsync(new ProfilePage(Page));
    }
}
