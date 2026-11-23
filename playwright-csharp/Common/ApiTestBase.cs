using System.Text.Json;
using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Base class for the ClimaNuvem REST API tests (<c>/api/v1</c>). Owns one Playwright
/// <see cref="IAPIRequestContext"/> per fixture and exposes the URL builders, a single request
/// helper, a single multipart upload helper, a problem+json assertion and a polling helper.
///
/// The SUT runs with <c>TEST_MODE=true</c>: any Bearer token is accepted, so <see cref="TestToken"/>
/// authenticates the test user and a missing header is the only unauthenticated case.
/// </summary>
public abstract class ApiTestBase
{
    protected const int NonExistentId = int.MaxValue;
    private const string ApiPrefix = "/api/v1";

    protected static readonly string TestToken = TestSettings.TestToken;

    private IPlaywright _playwright = null!;
    private IAPIRequestContext _api = null!;

    [OneTimeSetUp]
    public async Task CreateRequestContext()
    {
        _playwright = await Playwright.CreateAsync();
        _api = await _playwright.APIRequest.NewContextAsync(new APIRequestNewContextOptions
        {
            BaseURL = TestSettings.SutUrl,
            Timeout = TestSettings.HttpTimeoutMs,
        });
    }

    [OneTimeTearDown]
    public async Task DisposeRequestContext()
    {
        await _api.DisposeAsync();
        _playwright.Dispose();
    }

    // ── URLs (relative to the SUT base URL) ──────────────────────────────

    /// <summary>Path under the versioned API prefix; empty or starting with "/".</summary>
    protected static string ApiUrl(string path = "") => ApiPrefix + path;

    /// <summary>The analyses collection; <paramref name="suffix"/> is empty or a query string such as "?page=1".</summary>
    protected static string AnalysesUrl(string suffix = "") => ApiUrl("/analyses") + suffix;

    protected static string AnalysisUrl(int id) => ApiUrl($"/analyses/{id}");

    protected static string AnalysisImageUrl(int id) => AnalysisUrl(id) + "/image";

    // ── Requests ─────────────────────────────────────────────────────────

    /// <summary>The single request helper: every call in the suite goes through here.</summary>
    protected async Task<ApiResponse> SendAsync(
        string method, string url, bool auth = true, object? json = null, IFormData? form = null)
    {
        var options = new APIRequestContextOptions { Method = method };
        if (auth)
        {
            options.Headers = new Dictionary<string, string> { ["Authorization"] = $"Bearer {TestToken}" };
        }
        if (json is not null)
        {
            options.DataObject = json;
        }
        if (form is not null)
        {
            options.Multipart = form;
        }

        var response = await _api.FetchAsync(url, options);
        try
        {
            return new ApiResponse(response.Status, response.Headers, await response.BodyAsync());
        }
        finally
        {
            await response.DisposeAsync();
        }
    }

    protected Task<ApiResponse> GetAsync(string url, bool auth = true) => SendAsync("GET", url, auth);

    protected Task<ApiResponse> DeleteAsync(string url, bool auth = true) => SendAsync("DELETE", url, auth);

    protected Task<ApiResponse> PatchStatusAsync(string url, string status, bool auth = true) =>
        SendAsync("PATCH", url, auth, json: new { status });

    /// <summary>
    /// Multipart <c>POST /api/v1/analyses</c> with camelCase fields. A null <paramref name="image"/>
    /// omits the file part; a null <paramref name="includeExplainability"/> omits that field.
    /// </summary>
    protected Task<ApiResponse> UploadAsync(
        byte[]? image,
        string location = "Test Location",
        string filename = "test.jpg",
        string contentType = "image/jpeg",
        bool? includeExplainability = null,
        IReadOnlyDictionary<string, string>? extraFields = null,
        bool auth = true)
    {
        var form = _api.CreateFormData();
        if (image is not null)
        {
            form.Set("file", new FilePayload { Name = filename, MimeType = contentType, Buffer = image });
        }
        form.Set("location", location);
        if (includeExplainability is { } explain)
        {
            form.Set("includeExplainability", explain);
        }
        foreach (var (name, value) in extraFields ?? new Dictionary<string, string>())
        {
            form.Set(name, value);
        }
        return SendAsync("POST", AnalysesUrl(), auth, form: form);
    }

    // ── Fixtures and shared flows ────────────────────────────────────────

    protected static long Unique() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

    /// <summary>Uploads a tiny valid JPEG and returns the new analysis id.</summary>
    protected async Task<int> CreateAnalysisAsync(string location)
    {
        var response = await UploadAsync(TestImages.Tiny(), location);
        Assert.That(response.Status, Is.EqualTo(202), $"Upload failed: {response.Text}");
        return response.Json.GetProperty("id").GetInt32();
    }

    protected async Task DeleteAllAnalysesAsync()
    {
        var response = await DeleteAsync(AnalysesUrl());
        Assert.That(response.Status, Is.EqualTo(204), "DELETE /analyses must clear the test user's data");
    }

    /// <summary>Lists the test user's analyses (first page of up to 100).</summary>
    protected async Task<JsonElement> ListAnalysesAsync(string query = "?size=100")
    {
        var response = await GetAsync(AnalysesUrl(query));
        Assert.That(response.Status, Is.EqualTo(200), response.Text);
        return response.Json;
    }

    /// <summary>
    /// Polls <c>GET /analyses/{id}</c> until it is completed or cancelled, or the timeout elapses,
    /// and returns the last analysis seen.
    /// </summary>
    protected Task<JsonElement> WaitForTerminalStatusAsync(int id, int? timeoutMs = null) =>
        PollUntilAsync(
            async () =>
            {
                var response = await GetAsync(AnalysisUrl(id));
                Assert.That(response.Status, Is.EqualTo(200), response.Text);
                return response.Json;
            },
            analysis => analysis.GetProperty("status").GetString() is "completed" or "cancelled",
            timeoutMs ?? TestSettings.AnalysisTimeoutMs);

    /// <summary>Polls <paramref name="probe"/> every few seconds until <paramref name="done"/> holds; returns the last value.</summary>
    protected static async Task<T> PollUntilAsync<T>(
        Func<Task<T>> probe, Func<T, bool> done, int timeoutMs, int pollMs = 2000)
    {
        var deadline = DateTime.UtcNow.AddMilliseconds(timeoutMs);
        while (true)
        {
            var value = await probe();
            if (done(value) || DateTime.UtcNow >= deadline)
            {
                return value;
            }
            await Task.Delay(pollMs);
        }
    }

    // ── Assertions ───────────────────────────────────────────────────────

    /// <summary>Asserts the uniform <c>application/problem+json</c> error: HTTP status and machine-code <c>detail</c>.</summary>
    protected static void AssertProblem(ApiResponse response, int status, string detail)
    {
        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Status, Is.EqualTo(status), $"HTTP status (body: {response.Text})");
            Assert.That(response.Header("Content-Type"), Does.StartWith("application/problem+json"));
            var body = response.Json;
            Assert.That(body.GetProperty("status").GetInt32(), Is.EqualTo(status), "problem 'status'");
            Assert.That(body.GetProperty("detail").GetString(), Is.EqualTo(detail), "problem 'detail' machine code");
        }
    }

    /// <summary>Asserts a 405 response whose <c>Allow</c> header lists every given method.</summary>
    protected static void AssertMethodNotAllowed(ApiResponse response, params string[] allowedMethods)
    {
        Assert.That(response.Status, Is.EqualTo(405));
        var allow = (response.Header("Allow") ?? "")
            .Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);
        Assert.That(allow, Is.SupersetOf(allowedMethods).IgnoreCase, "Allow header");
    }

    protected static bool ContainsId(JsonElement analyses, int id) =>
        analyses.EnumerateArray().Any(a => a.GetProperty("id").GetInt32() == id);
}
