using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// POST /api/v1/analyses (202 Accepted + Location + {id, status}) and 405 handling. Runs with
/// DISABLE_WORKER=true, so uploads stay in 'analyzing' and no Ollama is needed.
/// </summary>
[TestFixture]
public class AnalysisTests : ApiTestBase
{
    [Test(Description = "Upload returns 202, a Location header and {id, status:'analyzing'}")]
    public async Task UploadReturnsAcceptedWithLocation()
    {
        var response = await UploadAsync(TestImages.Tiny());
        var body = response.Json;
        var id = body.GetProperty("id").GetInt32();

        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Status, Is.EqualTo(202));
            Assert.That(id, Is.GreaterThan(0));
            Assert.That(body.GetProperty("status").GetString(), Is.EqualTo("analyzing"));
            Assert.That(body.TryGetProperty("analysis_id", out _), Is.False, "Legacy 'analysis_id' must be gone");
            Assert.That(response.Header("Location"), Does.EndWith($"/api/v1/analyses/{id}"));
        }
    }

    [Test(Description = "The location sent in the upload is stored on the created analysis")]
    public async Task UploadStoresLocation()
    {
        var location = $"Madrid, Spain {Unique()}";
        var id = await CreateAnalysisAsync(location);

        var analysis = await GetAsync(AnalysisUrl(id));

        Assert.That(analysis.Json.GetProperty("location").GetString(), Is.EqualTo(location));
    }

    [Test(Description = "Optional camelCase fields (fcmToken, latitude, longitude, includeExplainability) are accepted")]
    public async Task UploadAcceptsOptionalFields()
    {
        var optional = new Dictionary<string, string>
        {
            ["fcmToken"] = "test-fcm-token",
            ["latitude"] = "43.5322",
            ["longitude"] = "-5.6611",
        };

        var response = await UploadAsync(TestImages.Tiny(), "Gijon", includeExplainability: true, extraFields: optional);

        Assert.That(response.Status, Is.EqualTo(202), response.Text);
    }

    [Test(Description = "Two consecutive uploads produce distinct ids")]
    public async Task ConsecutiveUploadsHaveDistinctIds()
    {
        var first = await CreateAnalysisAsync("Location A");
        var second = await CreateAnalysisAsync("Location B");

        Assert.That(second, Is.Not.EqualTo(first));
    }

    [Test(Description = "PUT /api/v1/analyses returns 405 and an Allow header with GET, POST, DELETE")]
    public async Task UnsupportedMethodOnCollectionReturns405()
    {
        var response = await SendAsync("PUT", AnalysesUrl());

        AssertMethodNotAllowed(response, "GET", "POST", "DELETE");
    }

    [Test(Description = "POST /api/v1/analyses/{id} returns 405 and an Allow header with GET, PATCH, DELETE")]
    public async Task PostOnSingleAnalysisReturns405()
    {
        var id = await CreateAnalysisAsync("Method Check City");

        var response = await SendAsync("POST", AnalysisUrl(id));

        AssertMethodNotAllowed(response, "GET", "PATCH", "DELETE");
    }
}
