using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// API tests for the public health-check endpoints that require no
/// authentication, mirroring selenium-java's <c>TestApiPing</c>:
///   GET /ping  — liveness probe
///   GET /      — service status response
/// </summary>
[TestFixture]
public class PingTests : ApiTestBase
{
    [Test]
    [Description("GET /ping returns HTTP 200 with ping:pong payload")]
    public async Task PingEndpointReturnsPingPong()
    {
        Assert.That(await GetStatusAsync(RootUrl("/ping")), Is.EqualTo(200), "Expected HTTP 200 from /ping");

        var body = await GetJsonAsync(RootUrl("/ping"));
        Assert.That(body.GetProperty("ping").GetString(), Is.EqualTo("pong"), "'ping' field must equal 'pong'");
    }

    [Test]
    [Description("GET / returns HTTP 200 with service status payload")]
    public async Task RootEndpointReturnsServiceStatus()
    {
        Assert.That(await GetStatusAsync(RootUrl("/")), Is.EqualTo(200), "Expected HTTP 200 from /");

        var body = await GetJsonAsync(RootUrl("/"));
        Assert.That(
            body.GetProperty("service").GetString(), Is.EqualTo("ClimaNuvem API"),
            "'service' field must identify the API");
        Assert.That(body.GetProperty("status").GetString(), Is.EqualTo("ok"), "'status' field must equal 'ok'");
    }
}
