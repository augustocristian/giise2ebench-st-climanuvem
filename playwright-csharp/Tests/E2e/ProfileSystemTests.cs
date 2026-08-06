using PlaywrightStClimanuvem.Common;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Tests.E2e;

/// <summary>
/// Browser system tests for profile configuration, derived from the same
/// hierarchical test design as selenium-java's <c>TestProfileSystem</c>.
///
/// Unlike the Python/Cypress ports of this suite, no manual per-account
/// session isolation is needed here: <c>[TestCaseSource]</c> gives each
/// account row its own NUnit test instance, and <see cref="BrowserTestBase"/>
/// (built on Playwright's <c>PageTest</c>) already provisions a fresh
/// incognito context per test instance — exactly matching selenium-java's
/// fresh-ChromeDriver-per-<c>@ParameterizedTest</c>-row behavior.
/// </summary>
[TestFixture]
public class ProfileSystemTests : BrowserTestBase
{
    private const string Username0 = "";
    private const string Username2 = "ab";
    private const string Username20A = "perfilPrueba12345678";
    private const string Username20B = "perfilPrueba87654321";
    private const string Username21 = "perfilPrueba123456789";

    private static IEnumerable<TestAccount> ProfileAccountsSource() => TestAccountsData.ProfileAccounts();

    [Test]
    [Description("Guest session - theme and language preferences can be selected")]
    public async Task GuestSessionThemeAndLanguagePreferencesCanBeSelected()
    {
        var profilePage = await OpenGuestProfileAsync();
        await AssertThemeAndLanguagePreferencesSelectableAsync(profilePage);
    }

    [TestCaseSource(nameof(ProfileAccountsSource))]
    [Description("Authenticated session - delete account opens confirmation and can be cancelled")]
    public async Task AuthenticatedDeleteAccountShowsConfirmationAndCanBeCancelled(TestAccount account)
    {
        var profilePage = await OpenAuthenticatedProfileAsync(account);
        await profilePage.OpenDeleteAccountDialogAsync();

        Assert.That(await profilePage.IsDeleteConfirmVisibleAsync(), Is.True, "Delete account must open a confirmation dialog");

        await profilePage.CancelDeleteAccountAsync();
        Assert.That(await profilePage.IsDeleteConfirmVisibleAsync(), Is.False, "Delete confirmation must close after cancelling");
    }

    [TestCaseSource(nameof(ProfileAccountsSource))]
    [Description("Authenticated session - username length rules are enforced")]
    public async Task AuthenticatedUsernameLengthRulesAreEnforced(TestAccount account)
    {
        var profilePage = await OpenAuthenticatedProfileAsync(account);
        var validUsername20 = Username20DifferentFrom(await profilePage.CurrentUsernameAsync());

        await profilePage.UpdateUsernameAsync(validUsername20);
        await profilePage.WaitForProfileFeedbackAsync();
        await profilePage.CloseProfileFeedbackAsync();
        Assert.That(
            await profilePage.IsUsernameSectionVisibleAsync(), Is.True,
            "Twenty-character username must be accepted and keep the user on Profile");

        await profilePage.SetUsernameAsync(Username0);
        Assert.That(
            await profilePage.IsSaveButtonEnabledAsync(), Is.False, "Zero-character username must keep the save action disabled");

        await profilePage.SetUsernameAsync(Username2);
        Assert.That(
            await profilePage.IsSaveButtonEnabledAsync(), Is.False, "Two-character username must keep the save action disabled");

        await profilePage.SetUsernameAsync(Username21);
        Assert.That(
            await profilePage.IsSaveButtonEnabledAsync(), Is.False,
            "Twenty-one-character username must keep the save action disabled");
    }

    [TestCaseSource(nameof(ProfileAccountsSource))]
    [Description("Authenticated session - theme and language preferences can be selected")]
    public async Task AuthenticatedThemeAndLanguagePreferencesCanBeSelected(TestAccount account)
    {
        var profilePage = await OpenAuthenticatedProfileAsync(account);
        await AssertThemeAndLanguagePreferencesSelectableAsync(profilePage);
    }

    private async Task<ProfilePage> OpenGuestProfileAsync()
    {
        var home = await LoginAsGuestAsync();
        var profilePage = await home.ClickProfileAsync();
        await profilePage.WaitForGuestProfileAsync();
        Assert.That(await profilePage.IsGuestPreferencesVisibleAsync(), Is.True, "Guest profile must show guest preferences");
        return profilePage;
    }

    private async Task<ProfilePage> OpenAuthenticatedProfileAsync(TestAccount account)
    {
        var welcome = await OnWelcomePageAsync();
        var login = await welcome.ClickLoginButtonAsync();
        await login.LoginAsync(account.Email, account.Password);
        var home = await login.WaitForHomeAsync();
        var profilePage = await home.ClickProfileAsync();
        await profilePage.WaitForAuthenticatedProfileAsync();

        Assert.Multiple(async () =>
        {
            Assert.That(
                await profilePage.IsUsernameSectionVisibleAsync(), Is.True,
                "Authenticated profile must show username configuration");
            Assert.That(
                await profilePage.IsDeleteAccountVisibleAsync(), Is.True, "Authenticated profile must show delete-account action");
        });
        return profilePage;
    }

    private static async Task AssertThemeAndLanguagePreferencesSelectableAsync(ProfilePage profilePage)
    {
        await profilePage.ChooseLightThemeAsync();
        Assert.That(await profilePage.HasStoredThemeAsync("light"), Is.True, "Profile must store the light theme preference");

        await profilePage.ChooseDarkThemeAsync();
        Assert.That(await profilePage.HasStoredThemeAsync("dark"), Is.True, "Profile must store the dark theme preference");

        await profilePage.ChooseSystemThemeAsync();
        Assert.That(await profilePage.HasStoredThemeAsync("system"), Is.True, "Profile must store the system theme preference");

        await profilePage.ChooseEnglishLanguageAsync();
        Assert.That(await profilePage.HasStoredLanguageAsync("en"), Is.True, "Profile must store the English language preference");

        await profilePage.ChooseSpanishLanguageAsync();
        Assert.That(await profilePage.HasStoredLanguageAsync("es"), Is.True, "Profile must store the Spanish language preference");

        await profilePage.ChooseSystemLanguageAsync();
        Assert.That(await profilePage.HasStoredLanguageAsync("system"), Is.True, "Profile must store the system language preference");
    }

    private static string Username20DifferentFrom(string currentUsername) =>
        currentUsername == Username20A ? Username20B : Username20A;
}
