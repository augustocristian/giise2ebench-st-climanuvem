namespace PlaywrightStClimanuvem.Tests.Api;

/// <summary>
/// Authenticated image delivery (GET /api/v1/analyses/{id}/image) and the removed public
/// /uploads mount.
/// </summary>
[TestFixture]
public class ImageTests : ApiTestBase
{
    [Test(Description = "The owner gets the stored JPEG (image/jpeg, bytes start FF D8 FF)")]
    public async Task OwnerGetsJpeg()
    {
        var id = await CreateAnalysisAsync($"Image City {Unique()}");

        var response = await GetAsync(AnalysisImageUrl(id));

        using (Assert.EnterMultipleScope())
        {
            Assert.That(response.Status, Is.EqualTo(200));
            Assert.That(response.Header("Content-Type"), Does.StartWith("image/jpeg"));
            Assert.That(response.Body.Take(3), Is.EqualTo(new byte[] { 0xFF, 0xD8, 0xFF }), "JPEG magic bytes");
        }
    }

    [Test(Description = "The image endpoint without Authorization returns 401 NOT_AUTHENTICATED")]
    public async Task ImageRequiresAuthorization()
    {
        var id = await CreateAnalysisAsync("Image Auth City");

        var response = await GetAsync(AnalysisImageUrl(id), auth: false);

        AssertProblem(response, 401, "NOT_AUTHENTICATED");
    }

    [Test(Description = "The image of an unknown analysis returns 404 ANALYSIS_NOT_FOUND")]
    public async Task ImageUnknownIdReturns404()
    {
        var response = await GetAsync(AnalysisImageUrl(NonExistentId));

        AssertProblem(response, 404, "ANALYSIS_NOT_FOUND");
    }

    [Test(Description = "The public /uploads static mount no longer exists")]
    public async Task UploadsMountIsGone()
    {
        var response = await GetAsync("/uploads/anything.jpg", auth: false);

        Assert.That(response.Status, Is.EqualTo(404));
    }
}
