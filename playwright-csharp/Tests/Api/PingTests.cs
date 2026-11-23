namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>Public health-check endpoints (no authentication) and the removed legacy routes.</summary>
[TestFixture]
public class PingTests : ApiTestBase
{
    [Test(Description = "GET /api/v1/ping returns 200 with {\"ping\":\"pong\"}")]
    public async Task PingReturnsPong()
    {
        var response = await GetAsync(ApiUrl("/ping"), auth: false);

        Assert.That(response.Status, Is.EqualTo(200));
        Assert.That(response.Json.GetProperty("ping").GetString(), Is.EqualTo("pong"));
    }

    [TestCase("/", TestName = "RootReturnsServiceStatus_WithTrailingSlash")]
    [TestCase("", TestName = "RootReturnsServiceStatus_WithoutTrailingSlash")]
    public async Task RootReturnsServiceStatus(string path)
    {
        var response = await GetAsync(ApiUrl(path), auth: false);

        Assert.That(response.Status, Is.EqualTo(200));
        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Json.GetProperty("service").GetString(), Is.EqualTo("ClimaNuvem API"));
            Assert.That(response.Json.GetProperty("status").GetString(), Is.EqualTo("ok"));
        }
    }

    [Test(Description = "The unversioned GET /ping route no longer exists")]
    public async Task LegacyPingReturns404()
    {
        var response = await GetAsync("/ping", auth: false);

        Assert.That(response.Status, Is.EqualTo(404));
    }
}
