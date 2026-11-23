namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>DELETE /api/v1/analyses/{id} and DELETE /api/v1/analyses (both 204 with an empty body).</summary>
[TestFixture]
public class DeleteTests : ApiTestBase
{
    [Test(Description = "Deleting one analysis returns 204 with no body and the analysis disappears")]
    public async Task DeleteSingleReturns204()
    {
        var id = await CreateAnalysisAsync("Delete Me City");

        var response = await DeleteAsync(AnalysisUrl(id));

        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Status, Is.EqualTo(204));
            Assert.That(response.Body, Is.Empty);
            Assert.That(ContainsId(await ListAnalysesAsync(), id), Is.False, "Deleted analysis must not be listed");
            Assert.That((await GetAsync(AnalysisUrl(id))).Status, Is.EqualTo(404));
        }
    }

    [Test(Description = "Deleting a non-existent analysis returns 404 ANALYSIS_NOT_FOUND")]
    public async Task DeleteUnknownReturns404()
    {
        var response = await DeleteAsync(AnalysisUrl(NonExistentId));

        AssertProblem(response, 404, "ANALYSIS_NOT_FOUND");
    }

    [Test(Description = "DELETE on the collection returns 204 with no body and clears the history")]
    public async Task DeleteCollectionClearsHistory()
    {
        await CreateAnalysisAsync("Bulk Delete A");
        await CreateAnalysisAsync("Bulk Delete B");

        var response = await DeleteAsync(AnalysesUrl());

        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Status, Is.EqualTo(204));
            Assert.That(response.Body, Is.Empty);
            Assert.That((await ListAnalysesAsync()).GetArrayLength(), Is.Zero);
        }
    }

    [Test(Description = "DELETE on the collection returns 204 even when there is nothing to delete")]
    public async Task DeleteCollectionWhenEmptyReturns204()
    {
        await DeleteAllAnalysesAsync();

        var response = await DeleteAsync(AnalysesUrl());

        Assert.That(response.Status, Is.EqualTo(204));
    }
}
