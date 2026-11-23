using PlaywrightStClimanuvem.Common;
using PlaywrightStClimanuvem.Pages;

namespace PlaywrightStClimanuvem.Tests.E2e;

/// <summary>
/// Browser system tests for profile configuration, derived from the same
/// hierarchical test design as selenium-java's <c>TestProfileSystem</c>.
/// Each account row gets its own test instance and browser context, so no
/// manual session isolation is needed.
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
        await profilePage.ExpectFeedbackAsync("Delete Account?", "permanent");

        await profilePage.CancelDeleteAccountAsync();
    }

    [TestCaseSource(nameof(ProfileAccountsSource))]
    [Description("Authenticated session - username length rules are enforced")]
    public async Task AuthenticatedUsernameLengthRulesAreEnforced(TestAccount account)
    {
        var profilePage = await OpenAuthenticatedProfileAsync(account);
        var currentUsername = await profilePage.CurrentUsernameAsync();

        await profilePage.SaveUsernameAsync(currentUsername == Username20A ? Username20B : Username20A);
        await profilePage.ExpectFeedbackAsync("Profile updated", "updated successfully");
        await profilePage.DismissFeedbackAsync();
        await profilePage.ExpectUsernameSectionVisibleAsync();

        // Zero, two and twenty-one characters keep the save action disabled.
        foreach (var invalidUsername in new[] { Username0, Username2, Username21 })
        {
            await profilePage.SetUsernameAsync(invalidUsername);
            await profilePage.ExpectSaveDisabledAsync();
        }
    }

    [TestCaseSource(nameof(ProfileAccountsSource))]
    [Description("Authenticated session - theme and language preferences can be selected")]
    public async Task AuthenticatedThemeAndLanguagePreferencesCanBeSelected(TestAccount account)
    {
        var profilePage = await OpenAuthenticatedProfileAsync(account);
        await AssertThemeAndLanguagePreferencesSelectableAsync(profilePage);
    }

    private static async Task AssertThemeAndLanguagePreferencesSelectableAsync(ProfilePage profilePage)
    {
        foreach (var theme in Enum.GetValues<ThemeOption>())
        {
            await profilePage.ChooseThemeAsync(theme);
            await profilePage.ExpectStoredThemeAsync(theme);
        }

        foreach (var language in Enum.GetValues<LanguageOption>())
        {
            await profilePage.ChooseLanguageAsync(language);
            await profilePage.ExpectStoredLanguageAsync(language);
        }
    }
}
