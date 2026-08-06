using System.Text.Json;
using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// System tests for the real image-analysis flow, mirroring selenium-java's
/// <c>TestApiImageAnalysisSystem</c>.
///
/// These tests require the SUT deployed with the analysis worker enabled
/// and Ollama available (<c>sut/docker-compose.ollama-test.yml</c>). Run
/// them explicitly with:
///
///   REAL_OLLAMA_TESTS=true dotnet test --filter FullyQualifiedName~ImageAnalysisSystemTests
///
/// Without <c>REAL_OLLAMA_TESTS=true</c> every test here reports as
/// skipped (<c>Assert.Ignore</c>) — the direct equivalent of the Java
/// suite's <c>Assumptions.assumeTrue(...)</c> opt-in gate.
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
        await DeleteAllUserDataAsync();
    }

    [Test]
    [Description("BASE - Gallery/API JPG under 5 MB without explainability completes with cloud results")]
    public async Task BaseGalleryJpgUnderLimitWithoutExplainabilityCompletesWithCloudResults()
    {
        var upload = await UploadAndAssertAnalyzingAsync(
            CreateCloudyJpeg(), "base-gallery.jpg", "image/jpeg", "Base Gallery City", false);

        var completed = await WaitForCompletedAnalysisAsync(upload.GetProperty("analysis_id").GetInt32());
        var cloudTypes = completed.GetProperty("results").GetProperty("cloudTypes");
        Assert.That(cloudTypes.GetArrayLength(), Is.GreaterThan(0), "A valid cloudy JPG must complete with at least one cloud type");
    }

    [Test]
    [Description("2 - Camera-origin JPG is processed like a gallery upload")]
    public async Task CameraOriginJpgIsProcessedLikeGalleryUpload()
    {
        var upload = await UploadAndAssertAnalyzingAsync(
            CreateCloudyJpeg(), "camera-capture.jpg", "image/jpeg", "Camera City", false);

        var completed = await WaitForCompletedAnalysisAsync(upload.GetProperty("analysis_id").GetInt32());
        Assert.That(
            completed.GetProperty("status").GetString(), Is.EqualTo("completed"),
            "A camera-origin JPG reaches the same completed state as gallery uploads at API level");
    }

    [Test]
    [Description("3 - Upload with no selected file is rejected")]
    public async Task UploadWithNoSelectedFileIsRejected()
    {
        var status = await UploadWithoutFileStatusAsync(AnalysisUrl("/upload"), "No File City");
        Assert.That(status, Is.EqualTo(422), "Multipart uploads without a file must be rejected as an invalid request");
    }

    [Test]
    [Description("4 - Zero-byte image is rejected")]
    public async Task ZeroByteImageIsRejected()
    {
        var status = await UploadImageStatusAsync(
            AnalysisUrl("/upload"), CreateEmptyImageBytes(), "Empty Image City", "empty.jpg", "image/jpeg", false);
        Assert.That(status, Is.EqualTo(400), "Zero-byte images must be rejected with HTTP 400");
    }

    [Test]
    [Description("5 - Image larger than 5 MB is rejected")]
    public async Task ImageLargerThanFiveMbIsRejected()
    {
        var status = await UploadImageStatusAsync(
            AnalysisUrl("/upload"), CreateTooLargePayload(), "Too Large City", "too-large.jpg", "image/jpeg", false);
        Assert.That(status, Is.EqualTo(413), "Images above the 5 MB limit must be rejected with HTTP 413");
    }

    [Test]
    [Description("6 - Non-JPG upload is rejected")]
    public async Task NonJpgUploadIsRejected()
    {
        var status = await UploadImageStatusAsync(
            AnalysisUrl("/upload"), CreateNonJpegPayload(), "Wrong Format City", "not-a-jpg.txt", "text/plain", false);
        Assert.That(status, Is.GreaterThanOrEqualTo(400), "Non-JPG images must be rejected by the system design");
    }

    [Test]
    [Description("7 - Explainability with clouds completes with normalized bounding boxes")]
    public async Task ExplainabilityWithCloudsCompletesWithNormalizedBoundingBoxes()
    {
        var upload = await UploadAndAssertAnalyzingAsync(
            CreateCloudyJpeg(), "explainability-clouds.jpg", "image/jpeg", "Explainability City", true);

        var completed = await WaitForCompletedAnalysisAsync(upload.GetProperty("analysis_id").GetInt32());
        var cloudDetails = completed.GetProperty("results").GetProperty("cloudDetails");
        Assert.That(
            HasNormalizedBox(cloudDetails), Is.True,
            "Explainability enabled for a cloudy image must persist at least one normalized box");
    }

    [Test]
    [Description("8 - No-cloud JPG without explainability completes without boxes")]
    public async Task NoCloudJpgWithoutExplainabilityCompletesWithoutBoxes()
    {
        var upload = await UploadAndAssertAnalyzingAsync(
            CreateNoCloudJpeg(), "clear-sky.jpg", "image/jpeg", "Clear Sky City", false);

        var completed = await WaitForCompletedAnalysisAsync(upload.GetProperty("analysis_id").GetInt32());
        var results = completed.GetProperty("results");

        Assert.Multiple(() =>
        {
            Assert.That(IsNoCloudCompatible(results), Is.True, "A clear-sky image should produce no clouds or the no_cloud label");
            Assert.That(
                HasNormalizedBox(results.GetProperty("cloudDetails")), Is.False,
                "Explainability disabled must not require bounding boxes");
        });
    }

    private async Task<JsonElement> UploadAndAssertAnalyzingAsync(
        byte[] imageBytes, string filename, string contentType, string location, bool includeExplainability)
    {
        var response = await UploadImageAsync(AnalysisUrl("/upload"), imageBytes, location, filename, contentType, includeExplainability);
        Assert.That(response.StatusCode, Is.EqualTo(200), "Upload must return HTTP 200");

        var body = response.Json;
        Assert.Multiple(() =>
        {
            Assert.That(body.TryGetProperty("analysis_id", out _), Is.True, "Upload response must contain analysis_id");
            Assert.That(body.GetProperty("status").GetString(), Is.EqualTo("analyzing"), "Upload response must start in analyzing status");
            Assert.That(body.GetProperty("analysis_id").GetInt32(), Is.GreaterThan(0), "analysis_id must be positive");
        });
        return body;
    }

    private async Task<JsonElement> WaitForCompletedAnalysisAsync(int analysisId)
    {
        var analysis = await WaitForAnalysisTerminalStatusAsync(analysisId);
        Assert.That(analysis, Is.Not.Null, $"Analysis {analysisId} must appear in history before timeout");

        var status = analysis!.Value.GetProperty("status").GetString();
        Assert.That(status, Is.Not.EqualTo("cancelled"), $"Analysis {analysisId} unexpectedly cancelled - check the Ollama worker logs");
        Assert.That(status, Is.EqualTo("completed"), $"Analysis {analysisId} must complete successfully");
        return analysis.Value;
    }

    private static bool HasNormalizedBox(JsonElement cloudDetails)
    {
        foreach (var detail in cloudDetails.EnumerateArray())
        {
            if (!detail.TryGetProperty("box", out var box) || box.ValueKind != JsonValueKind.Array || box.GetArrayLength() != 4)
            {
                continue;
            }
            if (box.EnumerateArray().All(coordinate => coordinate.GetDouble() is >= 0.0 and <= 1.0))
            {
                return true;
            }
        }
        return false;
    }

    private static bool IsNoCloudCompatible(JsonElement results)
    {
        var cloudTypes = results.GetProperty("cloudTypes");
        if (cloudTypes.GetArrayLength() == 0)
        {
            return true;
        }
        return cloudTypes.EnumerateArray().Any(cloudType => cloudType.GetString() == "no_cloud");
    }
}
