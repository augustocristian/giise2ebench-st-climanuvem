using PlaywrightStClimanuvem.Common;

namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// API tests for the deletion endpoints, mirroring selenium-java's
/// <c>TestApiDelete</c>:
///   DELETE /analysis/{id}       — remove a single analysis (HTTP 200 or 404)
///   DELETE /analysis/user-data  — remove all analyses for the user (HTTP 200)
/// </summary>
[TestFixture]
public class DeleteTests : ApiTestBase
{
    private const int NonExistentId = int.MaxValue; // mirrors the Java fixture

    [Test]
    [Description("DELETE /analysis/{id} returns HTTP 200 and the analysis no longer appears in history")]
    public async Task DeleteSingleAnalysisReturns200()
    {
        var analysisId = await CreateAnalysisAsync("Delete Me City");

        var status = await DeleteStatusAuthAsync(AnalysisUrl($"/{analysisId}"));
        Assert.That(status, Is.EqualTo(200), "Deleting an existing analysis must return HTTP 200");

        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        Assert.That(
            ContainsByField(history, "id", analysisId), Is.False, "Deleted analysis must not appear in history");
    }

    [Test]
    [Description("DELETE /analysis/{id} returns HTTP 404 when the analysis does not exist")]
    public async Task DeleteNonExistentAnalysisReturns404()
    {
        var status = await DeleteStatusAuthAsync(AnalysisUrl($"/{NonExistentId}"));
        Assert.That(status, Is.EqualTo(404), "Deleting a non-existent analysis must return HTTP 404");
    }

    [Test]
    [Description("DELETE /analysis/user-data returns HTTP 200 and clears the user's entire history")]
    public async Task DeleteUserDataClearsHistory()
    {
        await CreateAnalysisAsync("Bulk Delete A");
        await CreateAnalysisAsync("Bulk Delete B");

        var status = await DeleteAllUserDataAsync();
        Assert.That(status, Is.EqualTo(200), "Deleting all user data must return HTTP 200");

        var history = await GetJsonAuthAsync(AnalysisUrl("/history"));
        Assert.That(history.GetArrayLength(), Is.EqualTo(0), "History must be empty after deleting all user data");
    }

    [Test]
    [Description("DELETE /analysis/user-data returns HTTP 200 even when the user has no data")]
    public async Task DeleteUserDataWhenEmptyReturns200()
    {
        await DeleteAllUserDataAsync();
        var status = await DeleteAllUserDataAsync();
        Assert.That(status, Is.EqualTo(200), "DELETE /user-data must return 200 even when there is nothing to delete");
    }
}
