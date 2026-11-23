using System.Text.RegularExpressions;
using Microsoft.Playwright;
using PlaywrightStClimanuvem.Common;
using static Microsoft.Playwright.Assertions;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Base for every screen Page Object. All shared behavior lives here:
/// resolving the visible element for a <c>data-testid</c>, click/fill helpers,
/// screen-readiness and feedback-dialog assertions. Timeouts come from the
/// Playwright defaults configured once in <see cref="BrowserTestBase"/>.
/// </summary>
public abstract class BasePage
{
    protected readonly IPage Page;

    protected BasePage(IPage page) => Page = page;

    /// <summary>Test id of this screen's feedback dialog (the <c>*-feedback</c> card).</summary>
    protected virtual string FeedbackTestId =>
        throw new NotSupportedException($"{GetType().Name} has no feedback dialog.");

    /// <summary>Asserts that the screen is mounted and usable.</summary>
    protected abstract Task ExpectReadyAsync();

    /// <summary>Waits until <paramref name="page"/> is ready and returns it.</summary>
    public static async Task<T> WhenReadyAsync<T>(T page) where T : BasePage
    {
        await page.ExpectReadyAsync();
        return page;
    }

    /// <summary>
    /// The visible element with the given test id. The app keeps previous stack
    /// screens mounted but hidden, so the same id can exist on several screens.
    /// </summary>
    protected ILocator ByTestId(string testId) =>
        Page.GetByTestId(testId).Filter(new LocatorFilterOptions { Visible = true });

    protected Task ClickAsync(string testId) => ByTestId(testId).ClickAsync();

    protected Task FillAsync(string testId, string text) => ByTestId(testId).FillAsync(text);

    protected Task ExpectVisibleAsync(string testId) => Expect(ByTestId(testId)).ToBeVisibleAsync();

    protected Task ExpectHiddenAsync(string testId) => Expect(ByTestId(testId)).ToBeHiddenAsync();

    protected Task ExpectValueAsync(string testId, string value) => Expect(ByTestId(testId)).ToHaveValueAsync(value);

    /// <summary>Asserts the feedback dialog is shown with exactly this title and a message containing the text.</summary>
    public async Task ExpectFeedbackAsync(string title, string messagePart)
    {
        await ExpectFeedbackTitleAsync(title);
        await Expect(FeedbackPart(TestIds.Dialog.Message)).ToContainTextAsync(messagePart);
    }

    /// <summary>Same as <see cref="ExpectFeedbackAsync(string, string)"/> but the message must match a pattern.</summary>
    public async Task ExpectFeedbackAsync(string title, Regex messagePattern)
    {
        await ExpectFeedbackTitleAsync(title);
        await Expect(FeedbackPart(TestIds.Dialog.Message)).ToContainTextAsync(messagePattern);
    }

    /// <summary>Accepts the feedback dialog and asserts it closes.</summary>
    public async Task DismissFeedbackAsync()
    {
        await FeedbackPart(TestIds.Dialog.AcceptButton).ClickAsync();
        await ExpectHiddenAsync(FeedbackTestId);
    }

    private Task ExpectFeedbackTitleAsync(string title) =>
        Expect(FeedbackPart(TestIds.Dialog.Title)).ToHaveTextAsync(title);

    private ILocator FeedbackPart(string dialogPartTestId) => ByTestId(FeedbackTestId).GetByTestId(dialogPartTestId);
}
