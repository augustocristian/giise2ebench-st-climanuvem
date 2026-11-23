namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// PATCH /api/v1/analyses/{id} with {"status":"cancelled"}. Runs with DISABLE_WORKER=true so
/// analyses stay 'analyzing', which makes cancellation deterministic without Ollama.
/// </summary>
[TestFixture]
public class CancelTests : ApiTestBase
{
    [Test(Description = "Cancelling an 'analyzing' analysis returns 200 and the updated object")]
    public async Task CancelReturnsUpdatedAnalysis()
    {
        var id = await CreateAnalysisAsync("Cancel Me City");

        var response = await PatchStatusAsync(AnalysisUrl(id), "cancelled");

        Assert.That(response.Status, Is.EqualTo(200), response.Text);
        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Json.GetProperty("id").GetInt32(), Is.EqualTo(id));
            Assert.That(response.Json.GetProperty("status").GetString(), Is.EqualTo("cancelled"));
        }
    }

    [Test(Description = "Cancelling an already cancelled analysis returns 409 ANALYSIS_NOT_CANCELLABLE")]
    public async Task CancelTwiceReturns409()
    {
        var id = await CreateAnalysisAsync("Double Cancel City");
        await PatchStatusAsync(AnalysisUrl(id), "cancelled");

        var second = await PatchStatusAsync(AnalysisUrl(id), "cancelled");

        AssertProblem(second, 409, "ANALYSIS_NOT_CANCELLABLE");
    }

    [Test(Description = "Cancelling a non-existent analysis returns 404 ANALYSIS_NOT_FOUND")]
    public async Task CancelUnknownReturns404()
    {
        var response = await PatchStatusAsync(AnalysisUrl(NonExistentId), "cancelled");

        AssertProblem(response, 404, "ANALYSIS_NOT_FOUND");
    }

    [Test(Description = "A status other than 'cancelled' returns 422 and leaves the analysis untouched")]
    public async Task PatchWithOtherStatusReturns422()
    {
        var id = await CreateAnalysisAsync("Bad Status City");

        var response = await PatchStatusAsync(AnalysisUrl(id), "completed");
        var stored = await GetAsync(AnalysisUrl(id));

        Assert.That(response.Status, Is.EqualTo(422));
        Assert.That(stored.Json.GetProperty("status").GetString(), Is.EqualTo("analyzing"));
    }
}
