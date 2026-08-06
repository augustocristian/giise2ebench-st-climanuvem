using System.Text.RegularExpressions;
using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Base for every Page Object screen class — one per SUT screen, same
/// split as selenium-java's <c>pages/BasePage.java</c>. Every "wait until
/// visible" need is routed through <see cref="VisibleMatchAsync"/>, a
/// manual poll (scan all current matches, retry every 200ms) rather than
/// Playwright's built-in strict-mode locator actions — several of our
/// locators (submit buttons, duplicated "Sistema" options) legitimately
/// match more than one element, which Playwright's strict mode rejects
/// outright; polling mirrors exactly what selenium-java's
/// <c>WebDriverWait</c> + "first/last visible" loops did.
/// </summary>
public abstract class BasePage
{
    protected const int TimeoutMs = 30_000;
    protected const string InteractiveSelector = "[role='button'], button, [tabindex]";
    private const int PollIntervalMs = 200;

    protected readonly IPage Page;

    protected BasePage(IPage page) => Page = page;

    // ── Shared locator factories ────────────────────────────────────────

    protected ILocator ByPartialText(string text) => Page.GetByText(text);

    protected ILocator ByPlaceholder(string placeholder) => Page.GetByPlaceholder(placeholder);

    /// <summary>Any button/role=button/tabindex element whose text contains `text`.</summary>
    protected ILocator InteractiveWithText(string text) =>
        Page.Locator(InteractiveSelector).Filter(new LocatorFilterOptions { HasText = text });

    /// <summary>Any element whose text matches any of `texts` — used for bilingual (es/en) labels.</summary>
    protected ILocator ByAnyText(params string[] texts) => Page.GetByText(AnyOf(texts));

    /// <summary>Any button/role=button/tabindex element whose text matches any of `texts`.</summary>
    protected ILocator InteractiveWithAnyText(params string[] texts) =>
        Page.Locator(InteractiveSelector).Filter(new LocatorFilterOptions { HasTextRegex = AnyOf(texts) });

    private static Regex AnyOf(IEnumerable<string> texts) =>
        new(string.Join('|', texts.Select(Regex.Escape)), RegexOptions.IgnoreCase);

    // ── Queries ──────────────────────────────────────────────────────────

    protected static async Task<bool> IsPresentAsync(ILocator locator) => await locator.CountAsync() > 0;

    protected static async Task<bool> IsVisibleAsync(ILocator locator)
    {
        var count = await locator.CountAsync();
        for (var i = 0; i < count; i++)
        {
            if (await locator.Nth(i).IsVisibleAsync())
            {
                return true;
            }
        }
        return false;
    }

    protected async Task<bool> HasInvalidRequiredInputAsync() =>
        await Page.EvaluateAsync<int>(
            "() => Array.from(document.querySelectorAll('input'))"
            + ".filter(el => el.required && !el.checkValidity()).length") > 0;

    protected async Task<bool> BodyTextContainsAnyAsync(IEnumerable<string> keywords)
    {
        var text = (await Page.EvaluateAsync<string>("() => document.body.innerText")).ToLowerInvariant();
        return keywords.Any(keyword => text.Contains(keyword.ToLowerInvariant()));
    }

    // ── Actions ──────────────────────────────────────────────────────────

    /// <summary>Waits for the first visible match of `locator` and returns it.</summary>
    protected static Task<ILocator> WaitForAsync(ILocator locator, int timeoutMs = TimeoutMs) =>
        VisibleMatchAsync(locator, timeoutMs, last: false);

    /// <summary>Waits for `locator` to have a visible match (first visible) and clicks it.</summary>
    protected static async Task ClickAsync(ILocator locator, int timeoutMs = TimeoutMs) =>
        await (await VisibleMatchAsync(locator, timeoutMs, last: false)).ClickAsync();

    /// <summary>
    /// Waits for `locator`, then clicks the *last visible* match among all
    /// of them — used where React Native Web renders multiple candidates
    /// and only the last one is the "real" interactive one (e.g. submit
    /// buttons, the second "Sistema" option under language preferences).
    /// </summary>
    protected static async Task ClickLastVisibleAsync(ILocator locator, int timeoutMs = TimeoutMs) =>
        await (await VisibleMatchAsync(locator, timeoutMs, last: true)).ClickAsync();

    protected static async Task FillAsync(ILocator locator, string text, int timeoutMs = TimeoutMs) =>
        await (await VisibleMatchAsync(locator, timeoutMs, last: false)).FillAsync(text);

    protected static async Task<string> InputValueAsync(ILocator locator) =>
        await (await VisibleMatchAsync(locator, TimeoutMs, last: false)).InputValueAsync();

    /// <summary>Polls `predicate` (a JS expression returning truthy/falsy) in-browser until it's truthy.</summary>
    protected async Task WaitUntilAsync(string jsPredicateExpression, int timeoutMs = TimeoutMs) =>
        await Page.WaitForFunctionAsync(jsPredicateExpression, null, new PageWaitForFunctionOptions { Timeout = timeoutMs });

    /// <summary>Scans all current matches of `locator` (first-to-last or last-to-first) every
    /// <see cref="PollIntervalMs"/>ms until one is visible, or throws once `timeoutMs` elapses —
    /// the direct equivalent of selenium-java's <c>wait.until(webDriver -> {...})</c> loops.</summary>
    protected static async Task<ILocator> VisibleMatchAsync(ILocator locator, int timeoutMs, bool last)
    {
        var deadline = DateTime.UtcNow.AddMilliseconds(timeoutMs);
        do
        {
            var count = await locator.CountAsync();
            var indices = last ? Enumerable.Range(0, count).Reverse() : Enumerable.Range(0, count);
            foreach (var i in indices)
            {
                var candidate = locator.Nth(i);
                if (await candidate.IsVisibleAsync())
                {
                    return candidate;
                }
            }
            await Task.Delay(PollIntervalMs);
        } while (DateTime.UtcNow < deadline);

        throw new TimeoutException($"No visible element found among matches before {timeoutMs}ms timeout");
    }
}
