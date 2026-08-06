using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// API tests for authentication enforcement across the API, mirroring
/// selenium-java's <c>TestApiAuth</c>:
///   GET  /test                 — requires a valid Bearer token
///   GET  /analysis/history     — requires a valid Bearer token
///   POST /analysis/upload      — requires a valid Bearer token
/// Missing Authorization header -> HTTP 403 (FastAPI HTTPBearer default).
/// </summary>
[TestFixture]
public class AuthTests : ApiTestBase
{
    [Test]
    [Description("GET /test without Authorization header returns HTTP 403")]
    public async Task TestEndpointRequiresAuth() =>
        Assert.That(
            await GetStatusAsync(RootUrl("/test")), Is.EqualTo(403),
            "/test must return 403 when no Authorization header is sent");

    [Test]
    [Description("GET /test with the test token returns HTTP 200 and user info")]
    public async Task TestEndpointWithValidTokenReturns200()
    {
        Assert.That(
            await GetStatusAuthAsync(RootUrl("/test")), Is.EqualTo(200),
            "/test must return 200 when a valid test token is provided");

        var body = await GetJsonAuthAsync(RootUrl("/test"));
        Assert.That(body.TryGetProperty("message", out _), Is.True, "Response must contain 'message'");
        Assert.That(body.TryGetProperty("user", out _), Is.True, "Response must contain 'user'");
        Assert.That(body.GetProperty("message").GetString(), Is.EqualTo("Test successful"), "'message' must equal 'Test successful'");
    }

    [Test]
    [Description("GET /analysis/history without Authorization header returns HTTP 403")]
    public async Task HistoryRequiresAuth() =>
        Assert.That(
            await GetStatusAsync(AnalysisUrl("/history")), Is.EqualTo(403),
            "/analysis/history must return 403 when no token is provided");

    [Test]
    [Description("POST /analysis/upload without Authorization header returns HTTP 403")]
    public async Task UploadRequiresAuth() =>
        Assert.That(
            await GetStatusAsync(AnalysisUrl("/upload")), Is.EqualTo(403),
            "/analysis/upload must return 403 when no token is provided");
}
