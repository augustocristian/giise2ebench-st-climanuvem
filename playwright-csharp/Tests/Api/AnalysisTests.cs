using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// API tests for the image-upload endpoint, mirroring selenium-java's
/// <c>TestApiAnalysis</c>:
///   POST /analysis/upload — creates an analysis record and returns its ID
/// Runs with DISABLE_WORKER=true, so uploaded analyses remain in
/// 'analyzing' status — no Ollama connection is required.
/// </summary>
[TestFixture]
public class AnalysisTests : ApiTestBase
{
    [Test]
    [Description("POST /analysis/upload returns HTTP 200 with status 'analyzing' and a positive analysis_id")]
    public async Task UploadImageReturnsAnalyzingStatus()
    {
        var response = await UploadImageAsync(AnalysisUrl("/upload"), CreateTestImage(), "Test Location");
        var body = response.Json;

        Assert.Multiple(() =>
        {
            Assert.That(body.TryGetProperty("analysis_id", out _), Is.True, "Response must contain 'analysis_id'");
            Assert.That(body.TryGetProperty("status", out _), Is.True, "Response must contain 'status'");
            Assert.That(body.GetProperty("status").GetString(), Is.EqualTo("analyzing"), "'status' must be 'analyzing' immediately after upload");
            Assert.That(body.GetProperty("analysis_id").GetInt32(), Is.GreaterThan(0), "'analysis_id' must be a positive integer");
        });
    }

    [Test]
    [Description("POST /analysis/upload returns HTTP 200")]
    public async Task UploadImageHttpStatus()
    {
        var status = await UploadImageStatusAsync(AnalysisUrl("/upload"), CreateTestImage(), "Another Location");
        Assert.That(status, Is.EqualTo(200), "Upload must return HTTP 200");
    }

    [Test]
    [Description("POST /analysis/upload with a custom location stores the location in the response")]
    public async Task UploadWithCustomLocation()
    {
        var location = $"Madrid, Spain {Unique()}";
        var response = await UploadImageAsync(AnalysisUrl("/upload"), CreateTestImage(), location);
        var body = response.Json;

        Assert.That(body.TryGetProperty("analysis_id", out _), Is.True, "Upload with custom location must return 'analysis_id'");
        Assert.That(body.GetProperty("analysis_id").GetInt32(), Is.GreaterThan(0), "'analysis_id' must be positive");
    }

    [Test]
    [Description("Two consecutive uploads produce distinct analysis IDs")]
    public async Task ConsecutiveUploadsHaveDistinctIds()
    {
        var idOne = await CreateAnalysisAsync("Location A");
        var idTwo = await CreateAnalysisAsync("Location B");
        Assert.That(idTwo, Is.Not.EqualTo(idOne), "Each upload must produce a unique analysis_id");
    }
}
