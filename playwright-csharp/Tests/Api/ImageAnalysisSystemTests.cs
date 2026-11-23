using System.Text.Json;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// System tests for the real image-analysis flow (worker enabled, Ollama available, see
/// <c>sut/docker-compose.ollama-test.yml</c>). Opt in explicitly:
///
///   REAL_OLLAMA_TESTS=true dotnet test --filter FullyQualifiedName~ImageAnalysisSystemTests
///
/// Without <c>REAL_OLLAMA_TESTS=true</c> every test reports as skipped.
/// </summary>
[TestFixture]
public class ImageAnalysisSystemTests : ApiTestBase
{
    [SetUp]
    public async Task RequireRealOllamaOptIn()
    {
        if (!TestSettings.RealOllamaTests)
        {
            Assert.Ignore("Real Ollama image-analysis tests are disabled. Set REAL_OLLAMA_TESTS=true to run them.");
        }
        await DeleteAllAnalysesAsync();
    }

    [Test(Description = "BASE - JPG under 5 MB without explainability completes with cloud results")]
    public async Task CloudyJpgCompletesWithCloudResults()
    {
        var completed = await UploadAndWaitAsync(TestImages.Cloudy(), "Base Gallery City", explain: false);

        var cloudTypes = completed.GetProperty("results").GetProperty("cloudTypes");
        Assert.That(cloudTypes.GetArrayLength(), Is.GreaterThan(0), "A cloudy JPG must report at least one cloud type");
    }

    [Test(Description = "2 - Camera-origin JPG is processed like a gallery upload")]
    public async Task CameraOriginJpgCompletes()
    {
        var completed = await UploadAndWaitAsync(TestImages.Cloudy(), "Camera City", explain: false, filename: "camera-capture.jpg");

        Assert.That(completed.GetProperty("status").GetString(), Is.EqualTo("completed"));
    }

    [Test(Description = "3 - Upload with no selected file is rejected with 422")]
    public async Task MissingFileIsRejected()
    {
        var response = await UploadAsync(null, "No File City");

        Assert.That(response.Status, Is.EqualTo(422), response.Text);
    }

    [Test(Description = "4 - Zero-byte image is rejected with 422 IMAGE_EMPTY")]
    public async Task ZeroByteImageIsRejected()
    {
        var response = await UploadAsync(Array.Empty<byte>(), "Empty Image City", "empty.jpg", includeExplainability: false);

        AssertProblem(response, 422, "IMAGE_EMPTY");
    }

    [Test(Description = "5 - Image larger than 5 MB is rejected with 413 IMAGE_TOO_LARGE_MAX_5MB")]
    public async Task ImageLargerThanFiveMbIsRejected()
    {
        var response = await UploadAsync(TestImages.TooLarge(), "Too Large City", "too-large.jpg", includeExplainability: false);

        AssertProblem(response, 413, "IMAGE_TOO_LARGE_MAX_5MB");
    }

    [Test(Description = "6 - Non-JPG upload is rejected with 415 INVALID_IMAGE_FORMAT_JPG_ONLY")]
    public async Task NonJpgUploadIsRejected()
    {
        var response = await UploadAsync(
            TestImages.NotAJpeg(), "Wrong Format City", "not-a-jpg.txt", "text/plain", includeExplainability: false);

        AssertProblem(response, 415, "INVALID_IMAGE_FORMAT_JPG_ONLY");
    }

    [Test(Description = "7 - Explainability with clouds completes with normalized bounding boxes")]
    public async Task ExplainabilityCompletesWithNormalizedBoxes()
    {
        var completed = await UploadAndWaitAsync(TestImages.Cloudy(), "Explainability City", explain: true);

        var cloudDetails = completed.GetProperty("results").GetProperty("cloudDetails");
        Assert.That(HasNormalizedBox(cloudDetails), Is.True, "At least one normalized box must be persisted");
    }

    [Test(Description = "8 - No-cloud JPG without explainability completes without boxes")]
    public async Task ClearSkyCompletesWithoutBoxes()
    {
        var completed = await UploadAndWaitAsync(TestImages.ClearSky(), "Clear Sky City", explain: false);

        var results = completed.GetProperty("results");
        using (Assert.EnterMultipleScope())
        {
            Assert.That(IsNoCloudCompatible(results), Is.True, "A clear sky must yield no clouds or the no_cloud label");
            Assert.That(HasNormalizedBox(results.GetProperty("cloudDetails")), Is.False, "No boxes without explainability");
        }
    }

    /// <summary>Uploads a valid JPG, checks the 202 'analyzing' answer and waits for the analysis to complete.</summary>
    private async Task<JsonElement> UploadAndWaitAsync(
        byte[] image, string location, bool explain, string filename = "image.jpg")
    {
        var upload = await UploadAsync(image, location, filename, includeExplainability: explain);
        Assert.That(upload.Status, Is.EqualTo(202), upload.Text);
        Assert.That(upload.Json.GetProperty("status").GetString(), Is.EqualTo("analyzing"));

        var id = upload.Json.GetProperty("id").GetInt32();
        var analysis = await WaitForTerminalStatusAsync(id);

        var status = analysis.GetProperty("status").GetString();
        Assert.That(status, Is.EqualTo("completed"), $"Analysis {id} must complete (check the Ollama worker logs)");
        return analysis;
    }

    private static bool HasNormalizedBox(JsonElement cloudDetails) =>
        cloudDetails.EnumerateArray().Any(detail =>
            detail.TryGetProperty("box", out var box)
            && box.ValueKind == JsonValueKind.Array
            && box.GetArrayLength() == 4
            && box.EnumerateArray().All(c => c.GetDouble() is >= 0.0 and <= 1.0));

    private static bool IsNoCloudCompatible(JsonElement results)
    {
        var cloudTypes = results.GetProperty("cloudTypes").EnumerateArray().ToArray();
        return cloudTypes.Length == 0 || cloudTypes.Any(t => t.GetString() == "no_cloud");
    }
}
