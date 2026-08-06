using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Page Object for profile configuration — mirrors both guest and
/// authenticated states, and both Spanish/English labels (the language
/// switcher changes the UI mid-test). Mirrors selenium-java's
/// <c>ProfilePage</c>.
/// </summary>
public sealed class ProfilePage : BasePage
{
    private static readonly string[] StatusFeedbackKeywords =
    [
        "perfil actualizado", "profile updated",
        "fallo de seguridad", "security failure",
        "error al eliminar datos", "error deleting data",
        "nombre de usuario debe tener", "username must be between",
    ];

    private const string UsernameInputSelector =
        "input[placeholder=\"Escribe tu nombre\"], input[placeholder=\"Enter your name\"]";

    private ProfilePage(IPage page) : base(page)
    {
    }

    public static async Task<ProfilePage> CreateAsync(IPage page)
    {
        var profilePage = new ProfilePage(page);
        await WaitForAsync(profilePage.ProfileTitle());
        return profilePage;
    }

    // ── Queries ──────────────────────────────────────────────────────────

    public Task<bool> IsGuestPreferencesVisibleAsync() => IsVisibleAsync(GuestPrefs());
    public Task<bool> IsUsernameSectionVisibleAsync() => IsVisibleAsync(UsernameSection());
    public Task<bool> IsDeleteAccountVisibleAsync() => IsVisibleAsync(DeleteAccount());
    public Task<bool> IsDeleteConfirmVisibleAsync() => IsVisibleAsync(ConfirmDelete());

    public Task<string> CurrentUsernameAsync() => InputValueAsync(UsernameInput());

    public async Task<bool> IsSaveButtonEnabledAsync()
    {
        var button = await WaitForAsync(SaveButton());
        const string script =
            "(el) => {"
            + "const target = el.closest(\"[role='button'],button,[tabindex]\") || el;"
            + "return target.getAttribute('aria-disabled') === 'true'"
            + " || target.disabled === true"
            + " || window.getComputedStyle(target).pointerEvents === 'none';";
        var disabled = await button.EvaluateAsync<bool>(script + "}");
        return !disabled;
    }

    public Task<bool> HasStoredThemeAsync(string value) => HasStoredValueAsync("appTheme", value);
    public Task<bool> HasStoredLanguageAsync(string value) => HasStoredValueAsync("appLanguage", value);

    // ── Actions ──────────────────────────────────────────────────────────

    public Task<ProfilePage> WaitForGuestProfileAsync() => WaitForVisibleThenReturnSelfAsync(GuestPrefs());

    public async Task<ProfilePage> WaitForAuthenticatedProfileAsync()
    {
        await WaitForAsync(UsernameSection());
        await WaitForAsync(DeleteAccount());
        return this;
    }

    public Task<ProfilePage> ChooseLightThemeAsync() => ChooseThemeAsync("Claro", "Light", "light");
    public Task<ProfilePage> ChooseDarkThemeAsync() => ChooseThemeAsync("Oscuro", "Dark", "dark");

    public async Task<ProfilePage> ChooseSystemThemeAsync()
    {
        await SelectOptionAsync("Sistema", "System", last: false);
        await WaitForStoredValueAsync("appTheme", "system");
        return this;
    }

    public async Task<ProfilePage> ChooseEnglishLanguageAsync()
    {
        await SelectOptionAsync("Inglés", "English", last: false);
        await WaitForStoredValueAsync("appLanguage", "en");
        return this;
    }

    public async Task<ProfilePage> ChooseSpanishLanguageAsync()
    {
        await SelectOptionAsync("Español", "Spanish", last: false);
        await WaitForStoredValueAsync("appLanguage", "es");
        return this;
    }

    public async Task<ProfilePage> ChooseSystemLanguageAsync()
    {
        // "Sistema"/"System" appears once under theme options and once under language
        // options — last:true picks the language one, mirroring the Java page object's
        // `lastMatch` flag on ProfilePage#clickOption.
        await SelectOptionAsync("Sistema", "System", last: true);
        await WaitForStoredValueAsync("appLanguage", "system");
        return this;
    }

    public async Task<ProfilePage> SetUsernameAsync(string username)
    {
        await FillAsync(UsernameInput(), username);
        return this;
    }

    public async Task<ProfilePage> UpdateUsernameAsync(string username)
    {
        await SetUsernameAsync(username);
        await ClickAsync(SaveButton());
        return this;
    }

    public async Task<ProfilePage> WaitForProfileFeedbackAsync()
    {
        var predicate =
            "() => {"
            + "const lower = document.body.innerText.toLowerCase();"
            + $"return {KeywordsJsArray(StatusFeedbackKeywords)}.some(k => lower.includes(k));"
            + "}";
        await WaitUntilAsync(predicate);
        return this;
    }

    public async Task<ProfilePage> CloseProfileFeedbackAsync()
    {
        await ClickAsync(InteractiveWithAnyText("Aceptar", "Accept", "OK"));
        var predicate =
            "() => {"
            + "const lower = document.body.innerText.toLowerCase();"
            + $"return !{KeywordsJsArray(StatusFeedbackKeywords)}.some(k => lower.includes(k));"
            + "}";
        await WaitUntilAsync(predicate);
        return this;
    }

    public async Task<ProfilePage> OpenDeleteAccountDialogAsync()
    {
        await ClickLastVisibleAsync(DeleteAccount());
        await WaitForAsync(ConfirmDelete());
        return this;
    }

    public async Task<ProfilePage> CancelDeleteAccountAsync()
    {
        await ClickAsync(Cancel());
        const string predicate =
            "() => {"
            + "const text = document.body.innerText;"
            + "return !text.includes('Sí, eliminar') && !text.includes('Yes, delete');"
            + "}";
        await WaitUntilAsync(predicate);
        return this;
    }

    // ── Internals ────────────────────────────────────────────────────────

    private ILocator ProfileTitle() => ByAnyText("Mi Perfil", "My Profile");
    private ILocator GuestPrefs() => ByAnyText("Preferencias de invitado", "Guest preferences");
    private ILocator UsernameSection() => ByAnyText("Nombre de usuario", "Username");
    private ILocator DeleteAccount() => InteractiveWithAnyText("Eliminar Cuenta", "Delete Account");
    private ILocator ConfirmDelete() => InteractiveWithAnyText("Sí, eliminar", "Yes, delete");
    private ILocator Cancel() => InteractiveWithAnyText("Cancelar", "Cancel");
    private ILocator SaveButton() => InteractiveWithAnyText("Guardar Cambios", "Save Changes");
    private ILocator UsernameInput() => Page.Locator(UsernameInputSelector);

    private async Task<ProfilePage> ChooseThemeAsync(string es, string en, string storedValue)
    {
        await SelectOptionAsync(es, en, last: false);
        await WaitForStoredValueAsync("appTheme", storedValue);
        return this;
    }

    private async Task SelectOptionAsync(string es, string en, bool last)
    {
        var option = await VisibleMatchAsync(InteractiveWithAnyText(es, en), TimeoutMs, last);
        await option.ClickAsync();
    }

    private async Task WaitForStoredValueAsync(string key, string expected)
    {
        var predicate = $"() => window.localStorage.getItem('{key}') === '{expected}'";
        await WaitUntilAsync(predicate);
    }

    private async Task<bool> HasStoredValueAsync(string key, string expected) =>
        await Page.EvaluateAsync<string?>("(k) => window.localStorage.getItem(k)", key) == expected;

    private async Task<ProfilePage> WaitForVisibleThenReturnSelfAsync(ILocator locator)
    {
        await WaitForAsync(locator);
        return this;
    }

    private static string KeywordsJsArray(IEnumerable<string> keywords) =>
        "[" + string.Join(',', keywords.Select(k => $"'{k}'")) + "]";
}
