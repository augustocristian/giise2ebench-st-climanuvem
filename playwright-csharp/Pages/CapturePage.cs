using Microsoft.Playwright;

namespace PlaywrightStClimanuvem.Pages;

/// <summary>
/// Page Object for the Capture (image-upload) screen. <see cref="CreateAsync"/>
/// waits until the "Tomar Foto" card is visible. Mirrors selenium-java's
/// <c>CapturePage</c>.
/// </summary>
public sealed class CapturePage : BasePage
{
    private const string CameraCardText = "Tomar Foto";
    private const string GalleryCardText = "Galería";
    private const string ExplainabilityText = "Explicabilidad";
    private const string FormatsInfoText = "Formatos soportados";
    private const string PageHeaderText = "Analizar Imagen";

    private CapturePage(IPage page) : base(page)
    {
    }

    public static async Task<CapturePage> CreateAsync(IPage page)
    {
        var capturePage = new CapturePage(page);
        await WaitForAsync(capturePage.CameraCard());
        return capturePage;
    }

    // ── Queries ──────────────────────────────────────────────────────────

    public Task<bool> IsCameraOptionVisibleAsync() => IsPresentAsync(CameraCard());
    public Task<bool> IsGalleryOptionVisibleAsync() => IsPresentAsync(ByPartialText(GalleryCardText));
    public Task<bool> IsExplainabilityVisibleAsync() => IsPresentAsync(ByPartialText(ExplainabilityText));
    public Task<bool> IsFormatsInfoVisibleAsync() => IsPresentAsync(ByPartialText(FormatsInfoText));
    public Task<bool> IsPageHeaderVisibleAsync() => IsPresentAsync(ByPartialText(PageHeaderText));

    private ILocator CameraCard() => ByPartialText(CameraCardText);
}
