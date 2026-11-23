using Microsoft.Playwright;
using PlaywrightStClimanuvem.Common;
using static Microsoft.Playwright.Assertions;

namespace PlaywrightStClimanuvem.Pages;

public enum ThemeOption { Light, Dark, System }

public enum LanguageOption { English, Spanish, System }

/// <summary>Profile screen, in its guest and authenticated variants.</summary>
public sealed class ProfilePage(IPage page) : BasePage(page)
{
    protected override string FeedbackTestId => TestIds.Profile.Feedback;

    protected override Task ExpectReadyAsync() => ExpectVisibleAsync(TestIds.Profile.Title);

    public Task ExpectGuestViewAsync() => ExpectVisibleAsync(TestIds.Profile.GuestPreferences);

    public async Task ExpectAuthenticatedViewAsync()
    {
        await ExpectVisibleAsync(TestIds.Profile.UsernameSection);
        await ExpectVisibleAsync(TestIds.Profile.DeleteAccountButton);
    }

    public Task ExpectUsernameSectionVisibleAsync() => ExpectVisibleAsync(TestIds.Profile.UsernameSection);

    // Username

    public Task<string> CurrentUsernameAsync() => ByTestId(TestIds.Profile.UsernameInput).InputValueAsync();

    public Task SetUsernameAsync(string username) => FillAsync(TestIds.Profile.UsernameInput, username);

    public async Task SaveUsernameAsync(string username)
    {
        await SetUsernameAsync(username);
        await ClickAsync(TestIds.Profile.SaveButton);
    }

    public Task ExpectSaveDisabledAsync() => Expect(ByTestId(TestIds.Profile.SaveButton)).ToBeDisabledAsync();

    // Delete account

    public async Task OpenDeleteAccountDialogAsync()
    {
        await ClickAsync(TestIds.Profile.DeleteAccountButton);
        await ExpectVisibleAsync(TestIds.Profile.DeleteConfirmButton);
    }

    public async Task CancelDeleteAccountAsync()
    {
        await ClickAsync(TestIds.Profile.DeleteCancelButton);
        await ExpectHiddenAsync(TestIds.Profile.DeleteConfirmButton);
    }

    // Preferences

    public Task ChooseThemeAsync(ThemeOption theme) => ClickAsync(theme switch
    {
        ThemeOption.Light => TestIds.Profile.ThemeLight,
        ThemeOption.Dark => TestIds.Profile.ThemeDark,
        _ => TestIds.Profile.ThemeSystem,
    });

    public Task ChooseLanguageAsync(LanguageOption language) => ClickAsync(language switch
    {
        LanguageOption.English => TestIds.Profile.LanguageEnglish,
        LanguageOption.Spanish => TestIds.Profile.LanguageSpanish,
        _ => TestIds.Profile.LanguageSystem,
    });

    public Task ExpectStoredThemeAsync(ThemeOption theme) =>
        ExpectStoredAsync("appTheme", theme.ToString().ToLowerInvariant());

    public Task ExpectStoredLanguageAsync(LanguageOption language) => ExpectStoredAsync(
        "appLanguage",
        language switch { LanguageOption.English => "en", LanguageOption.Spanish => "es", _ => "system" });

    private Task ExpectStoredAsync(string key, string value) =>
        Page.WaitForFunctionAsync("([k, v]) => window.localStorage.getItem(k) === v", new[] { key, value });
}
