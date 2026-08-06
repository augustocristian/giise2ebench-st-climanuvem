using System.Net.Http.Headers;
using System.Text.Json;

namespace PlaywrightStClimanuvem.Common;

/// <summary>
/// Base class for the ClimaNuvem API test suite. Handles HTTP plumbing,
/// Bearer-token auth, multipart image upload, and common fixture creation.
/// Mirrors selenium-java's <c>BaseApiClass</c>.
///
/// The SUT must be started with <c>TEST_MODE=true</c> so that requests
/// bearing <see cref="TestToken"/> bypass Firebase verification (see
/// <c>sut/docker-compose.test.yml</c>).
/// </summary>
public abstract class ApiTestBase
{
    protected static readonly string SutUrl = TestSettings.SutUrl;
    protected static readonly string TestToken = TestSettings.TestToken;

    private static HttpClient _client = null!;

    [OneTimeSetUp]
    public void SetUpClient()
    {
        _client = new HttpClient { Timeout = TimeSpan.FromMilliseconds(TestSettings.HttpTimeoutMs) };
        TestContext.Progress.WriteLine($"API base URL: {SutUrl}");
    }

    [OneTimeTearDown]
    public void TearDownClient() => _client.Dispose();

    // ── URL builders ─────────────────────────────────────────────────────

    protected static string AnalysisUrl(string path) => $"{SutUrl}/analysis{path}";

    protected static string RootUrl(string path) => $"{SutUrl}{path}";

    // ── Unauthenticated HTTP ─────────────────────────────────────────────

    protected static async Task<int> GetStatusAsync(string url)
    {
        using var response = await _client.GetAsync(url);
        return (int)response.StatusCode;
    }

    protected static async Task<JsonElement> GetJsonAsync(string url)
    {
        var body = await _client.GetStringAsync(url);
        return JsonDocument.Parse(body).RootElement;
    }

    // ── Authenticated HTTP ───────────────────────────────────────────────

    private static HttpRequestMessage AuthRequest(HttpMethod method, string url)
    {
        var request = new HttpRequestMessage(method, url);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", TestToken);
        return request;
    }

    protected static async Task<int> GetStatusAuthAsync(string url)
    {
        using var response = await _client.SendAsync(AuthRequest(HttpMethod.Get, url));
        return (int)response.StatusCode;
    }

    protected static async Task<JsonElement> GetJsonAuthAsync(string url)
    {
        using var response = await _client.SendAsync(AuthRequest(HttpMethod.Get, url));
        var body = await response.Content.ReadAsStringAsync();
        return JsonDocument.Parse(body).RootElement;
    }

    protected static async Task<int> DeleteStatusAuthAsync(string url)
    {
        using var response = await _client.SendAsync(AuthRequest(HttpMethod.Delete, url));
        return (int)response.StatusCode;
    }

    protected static async Task<int> PatchStatusAuthAsync(string url)
    {
        using var response = await _client.SendAsync(AuthRequest(HttpMethod.Patch, url));
        return (int)response.StatusCode;
    }

    // ── Multipart image upload ──────────────────────────────────────────

    protected static async Task<ApiResponse> UploadImageAsync(
        string url,
        byte[] imageBytes,
        string location,
        string filename = "test.jpg",
        string contentType = "image/jpeg",
        bool? includeExplainability = null)
    {
        using var request = AuthRequest(HttpMethod.Post, url);
        using var content = new MultipartFormDataContent();
        var fileContent = new ByteArrayContent(imageBytes);
        fileContent.Headers.ContentType = MediaTypeHeaderValue.Parse(contentType);
        content.Add(fileContent, "file", filename);
        content.Add(new StringContent(location), "location");
        if (includeExplainability is { } value)
        {
            content.Add(new StringContent(value.ToString().ToLowerInvariant()), "include_explainability");
        }
        request.Content = content;

        using var response = await _client.SendAsync(request);
        var body = await response.Content.ReadAsStringAsync();
        return new ApiResponse((int)response.StatusCode, body);
    }

    protected static async Task<int> UploadImageStatusAsync(
        string url,
        byte[] imageBytes,
        string location,
        string filename = "test.jpg",
        string contentType = "image/jpeg",
        bool? includeExplainability = null) =>
        (await UploadImageAsync(url, imageBytes, location, filename, contentType, includeExplainability)).StatusCode;

    protected static async Task<int> UploadWithoutFileStatusAsync(string url, string location)
    {
        using var request = AuthRequest(HttpMethod.Post, url);
        using var content = new MultipartFormDataContent { { new StringContent(location), "location" } };
        request.Content = content;
        using var response = await _client.SendAsync(request);
        return (int)response.StatusCode;
    }

    // ── JSON / history helpers ──────────────────────────────────────────

    protected static async Task<JsonElement?> FindAnalysisInHistoryAsync(int analysisId)
    {
        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        foreach (var entry in history.EnumerateArray())
        {
            if (entry.TryGetProperty("id", out var id) && id.GetInt32() == analysisId)
            {
                return entry;
            }
        }
        return null;
    }

    protected static async Task<JsonElement?> WaitForAnalysisTerminalStatusAsync(
        int analysisId, int? timeoutMs = null, int pollMs = 5000)
    {
        var deadline = DateTime.UtcNow.AddMilliseconds(timeoutMs ?? TestSettings.AnalysisTimeoutMs);
        JsonElement? lastSeen = null;

        while (DateTime.UtcNow < deadline)
        {
            lastSeen = await FindAnalysisInHistoryAsync(analysisId);
            if (lastSeen is { } entry
                && entry.TryGetProperty("status", out var status)
                && status.GetString() is "completed" or "cancelled")
            {
                return lastSeen;
            }
            await Task.Delay(pollMs);
        }

        return lastSeen;
    }

    protected static bool ContainsByField(JsonElement array, string field, object expected) =>
        array.EnumerateArray().Any(item =>
            item.TryGetProperty(field, out var value)
            && string.Equals(value.ToString(), expected.ToString(), StringComparison.Ordinal));

    // ── Test data helpers ────────────────────────────────────────────────

    protected static long Unique() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

    protected static byte[] CreateTestImage() => TestImages.CreateTestImage();
    protected static byte[] CreateCloudyJpeg() => TestImages.CreateCloudyJpeg();
    protected static byte[] CreateNoCloudJpeg() => TestImages.CreateNoCloudJpeg();
    protected static byte[] CreateEmptyImageBytes() => TestImages.CreateEmptyImageBytes();
    protected static byte[] CreateTooLargePayload() => TestImages.CreateTooLargePayload();
    protected static byte[] CreateNonJpegPayload() => TestImages.CreateNonJpegPayload();

    /// <summary>Uploads a test image to POST /analysis/upload and returns the assigned analysis ID.</summary>
    protected static async Task<int> CreateAnalysisAsync(string location)
    {
        var response = await UploadImageAsync(AnalysisUrl("/upload"), CreateTestImage(), location);
        return response.Json.GetProperty("analysis_id").GetInt32();
    }

    /// <summary>Deletes all analysis records for the test user via DELETE /analysis/user-data.</summary>
    protected static Task<int> DeleteAllUserDataAsync() => DeleteStatusAuthAsync(AnalysisUrl("/user-data"));
}
