using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// API tests for the analysis history endpoint, mirroring selenium-java's
/// <c>TestApiHistory</c>:
///   GET /analysis/history — returns all analyses for the authenticated user
/// A <c>[SetUp]</c> cleanup ensures the test user starts with an empty
/// history, making each scenario deterministic regardless of prior test
/// runs.
/// </summary>
[TestFixture]
public class HistoryTests : ApiTestBase
{
    [SetUp]
    public async Task CleanUpUserData() => await DeleteAllUserDataAsync();

    [Test]
    [Description("GET /analysis/history returns HTTP 200 with an empty list when the user has no analyses")]
    public async Task HistoryInitiallyEmpty()
    {
        Assert.That(await GetStatusAuthAsync(AnalysisUrl("/history")), Is.EqualTo(200), "History endpoint must return HTTP 200");

        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        Assert.That(history.GetArrayLength(), Is.EqualTo(0), "History must be empty for a fresh test user");
    }

    [Test]
    [Description("GET /analysis/history returns HTTP 200 and lists the uploaded analysis")]
    public async Task HistoryAfterUploadContainsEntry()
    {
        var analysisId = await CreateAnalysisAsync("Oviedo, Spain");

        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        Assert.That(history.GetArrayLength(), Is.GreaterThan(0), "History must contain the uploaded analysis");
        Assert.That(
            ContainsByField(history, "id", analysisId), Is.True, $"History must include the analysis with id={analysisId}");
    }

    [Test]
    [Description("GET /analysis/history returns entries with id, status, date, location, imageUrl, and results")]
    public async Task HistoryEntryHasRequiredFields()
    {
        await CreateAnalysisAsync("Test City");

        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        Assert.That(history.GetArrayLength(), Is.GreaterThan(0), "History must not be empty");

        var entry = history[0];
        Assert.Multiple(() =>
        {
            foreach (var field in new[] { "id", "status", "date", "location", "imageUrl", "results" })
            {
                Assert.That(entry.TryGetProperty(field, out _), Is.True, $"Entry must have '{field}'");
            }
        });
    }

    [Test]
    [Description("GET /analysis/history results block contains cloudTypes, cloudDetails, forecast, and warnings")]
    public async Task HistoryResultsBlockHasRequiredFields()
    {
        await CreateAnalysisAsync("Results Field City");

        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        Assert.That(history.GetArrayLength(), Is.GreaterThan(0), "History must not be empty");

        var results = history[0].GetProperty("results");
        Assert.Multiple(() =>
        {
            foreach (var field in new[] { "cloudTypes", "cloudDetails", "forecast", "warnings" })
            {
                Assert.That(results.TryGetProperty(field, out _), Is.True, $"results must have '{field}'");
            }
        });
    }
}
