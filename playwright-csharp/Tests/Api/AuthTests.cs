using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// Authentication enforcement: a missing Authorization header yields 401 NOT_AUTHENTICATED with a
/// Bearer challenge. In TEST_MODE any token is accepted, so an invalid token is not exercised.
/// </summary>
[TestFixture]
public class AuthTests : ApiTestBase
{
    [Test(Description = "GET /api/v1/test with the test token returns 200 and user info")]
    public async Task TestEndpointWithTokenReturnsUser()
    {
        var response = await GetAsync(ApiUrl("/test"));

        Assert.That(response.Status, Is.EqualTo(200));
        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Json.GetProperty("message").GetString(), Is.EqualTo("Test successful"));
            Assert.That(response.Json.TryGetProperty("user", out _), Is.True, "Response must contain 'user'");
        }
    }

    [TestCase("GET", "/test")]
    [TestCase("GET", "/analyses")]
    [TestCase("GET", "/analyses/1")]
    [TestCase("GET", "/analyses/1/image")]
    [TestCase("DELETE", "/analyses/1")]
    [TestCase("DELETE", "/analyses")]
    public async Task ProtectedEndpointRequiresAuthorization(string method, string path)
    {
        var response = await SendAsync(method, ApiUrl(path), auth: false);

        AssertUnauthenticated(response);
    }

    [Test(Description = "PATCH /api/v1/analyses/{id} without Authorization returns 401 NOT_AUTHENTICATED")]
    public async Task PatchRequiresAuthorization()
    {
        var response = await PatchStatusAsync(AnalysisUrl(1), "cancelled", auth: false);

        AssertUnauthenticated(response);
    }

    [Test(Description = "POST /api/v1/analyses without Authorization returns 401 NOT_AUTHENTICATED")]
    public async Task UploadRequiresAuthorization()
    {
        var response = await UploadAsync(TestImages.Tiny(), "No Auth City", auth: false);

        AssertUnauthenticated(response);
    }

    private static void AssertUnauthenticated(ApiResponse response)
    {
        AssertProblem(response, 401, "NOT_AUTHENTICATED");
        Assert.That(response.Header("WWW-Authenticate"), Does.StartWith("Bearer"));
    }
}
