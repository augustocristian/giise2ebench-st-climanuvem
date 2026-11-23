namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// GET /api/v1/analyses (list, pagination, X-Total-Count) and GET /api/v1/analyses/{id}. A
/// [SetUp] cleanup gives every test an empty history regardless of earlier runs.
/// </summary>
[TestFixture]
public class HistoryTests : ApiTestBase
{
    [SetUp]
    public async Task CleanUpUserData() => await DeleteAllAnalysesAsync();

    [Test(Description = "The list is empty for a user without analyses")]
    public async Task HistoryInitiallyEmpty()
    {
        var response = await GetAsync(AnalysesUrl());

        Assert.That(response.Status, Is.EqualTo(200));
        Assert.That(response.Json.GetArrayLength(), Is.Zero);
    }

    [Test(Description = "An uploaded analysis is listed with all required fields")]
    public async Task HistoryEntryHasRequiredFields()
    {
        var id = await CreateAnalysisAsync("Oviedo, Spain");

        var history = await ListAnalysesAsync();

        Assert.That(ContainsId(history, id), Is.True);
        var entry = history[0];
        using (Assert.EnterMultipleScope())
        {
            foreach (var field in new[] { "id", "status", "date", "location", "imageUrl", "results" })
            {
                Assert.That(entry.TryGetProperty(field, out _), Is.True, $"Entry must have '{field}'");
            }
            var results = entry.GetProperty("results");
            foreach (var field in new[] { "cloudTypes", "cloudDetails", "forecast", "warnings" })
            {
                Assert.That(results.TryGetProperty(field, out _), Is.True, $"results must have '{field}'");
            }
        }
    }

    [Test(Description = "GET /analyses/{id} returns 200 with the analysis object")]
    public async Task GetSingleReturnsAnalysis()
    {
        var id = await CreateAnalysisAsync("Single Get City");

        var response = await GetAsync(AnalysisUrl(id));
        var analysis = response.Json;

        Assert.That(response.Status, Is.EqualTo(200));
        using (Assert.EnterMultipleScope())
        {
            Assert.That(analysis.GetProperty("id").GetInt32(), Is.EqualTo(id));
            Assert.That(analysis.GetProperty("status").GetString(), Is.EqualTo("analyzing"));
            Assert.That(analysis.GetProperty("location").GetString(), Is.EqualTo("Single Get City"));
            Assert.That(analysis.GetProperty("imageUrl").GetString(), Is.EqualTo($"/api/v1/analyses/{id}/image"));
            Assert.That(analysis.TryGetProperty("results", out _), Is.True);
            Assert.That(analysis.GetProperty("date").GetString(), Does.EndWith("Z"), "ISO-8601 UTC timestamp");
        }
    }

    [Test(Description = "GET /analyses/{id} for an unknown id returns 404 ANALYSIS_NOT_FOUND")]
    public async Task GetSingleUnknownReturns404()
    {
        var response = await GetAsync(AnalysisUrl(NonExistentId));

        AssertProblem(response, 404, "ANALYSIS_NOT_FOUND");
    }

    [Test(Description = "page/size pagination returns newest first and X-Total-Count carries the total")]
    public async Task PaginationAndTotalCount()
    {
        var first = await CreateAnalysisAsync("Page City 1");
        var second = await CreateAnalysisAsync("Page City 2");
        var third = await CreateAnalysisAsync("Page City 3");

        var page0 = await GetAsync(AnalysesUrl("?page=0&size=2"));
        var page1 = await GetAsync(AnalysesUrl("?page=1&size=2"));
        var ids0 = page0.Json.EnumerateArray().Select(a => a.GetProperty("id").GetInt32()).ToArray();
        var ids1 = page1.Json.EnumerateArray().Select(a => a.GetProperty("id").GetInt32()).ToArray();

        using (Assert.EnterMultipleScope())
        {
            Assert.That(page0.Header("X-Total-Count"), Is.EqualTo("3"));
            Assert.That(ids0, Is.EqualTo(new[] { third, second }), "First page, newest first");
            Assert.That(ids1, Is.EqualTo(new[] { first }), "Second page holds the remainder");
        }
    }

    [TestCase("?size=0")]
    [TestCase("?size=101")]
    [TestCase("?page=-1")]
    public async Task OutOfRangePaginationReturns422(string query)
    {
        var response = await GetAsync(AnalysesUrl(query));

        Assert.That(response.Status, Is.EqualTo(422));
    }
}
