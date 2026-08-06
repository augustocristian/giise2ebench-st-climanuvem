using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// API tests for the cancellation endpoint, mirroring selenium-java's
/// <c>TestApiCancel</c>:
///   PATCH /analysis/{id}/cancel — cancel an in-progress analysis
/// Runs with DISABLE_WORKER=true so uploaded analyses stay in 'analyzing'
/// status, making cancellation deterministic without Ollama.
/// </summary>
[TestFixture]
public class CancelTests : ApiTestBase
{
    private const int NonExistentId = int.MaxValue; // mirrors the Java fixture

    [Test]
    [Description("PATCH /analysis/{id}/cancel returns HTTP 200 for an analysis in 'analyzing' status")]
    public async Task CancelAnalysisReturns200()
    {
        var analysisId = await CreateAnalysisAsync("Cancel Me City");
        var status = await PatchStatusAuthAsync(AnalysisUrl($"/{analysisId}/cancel"));
        Assert.That(status, Is.EqualTo(200), "Cancelling an 'analyzing' task must return HTTP 200");
    }

    [Test]
    [Description("PATCH /analysis/{id}/cancel returns HTTP 400 when the analysis is already cancelled")]
    public async Task CancelAlreadyCancelledReturns400()
    {
        var analysisId = await CreateAnalysisAsync("Double Cancel City");
        await PatchStatusAuthAsync(AnalysisUrl($"/{analysisId}/cancel"));

        var secondStatus = await PatchStatusAuthAsync(AnalysisUrl($"/{analysisId}/cancel"));
        Assert.That(secondStatus, Is.EqualTo(400), "Cancelling an already-cancelled analysis must return HTTP 400");
    }

    [Test]
    [Description("PATCH /analysis/{id}/cancel returns HTTP 404 for a non-existent analysis")]
    public async Task CancelNonExistentAnalysisReturns404()
    {
        var status = await PatchStatusAuthAsync(AnalysisUrl($"/{NonExistentId}/cancel"));
        Assert.That(status, Is.EqualTo(404), "Cancelling a non-existent analysis must return HTTP 404");
    }

    [Test]
    [Description("PATCH /analysis/{id}/cancel without Authorization header returns HTTP 403")]
    public async Task CancelRequiresAuth()
    {
        var analysisId = await CreateAnalysisAsync("Auth Check City");
        var status = await GetStatusAsync(AnalysisUrl($"/{analysisId}/cancel"));
        Assert.That(status, Is.EqualTo(403), "Cancel endpoint must return 403 when no token is provided");
    }
}
