package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;

/**
 * Page Object for the Capture (image-upload) screen.
 * <p>
 * Constructing this object waits until the "Tomar Foto" card is visible,
 * confirming that the screen has fully mounted.
 */
public class CapturePage extends BasePage {

    private static final By CAMERA_CARD        = byPartialText("Tomar Foto");
    private static final By GALLERY_CARD       = byPartialText("Galería");
    private static final By EXPLAINABILITY     = byPartialText("Explicabilidad");
    private static final By FORMATS_INFO       = byPartialText("Formatos soportados");
    private static final By PAGE_HEADER        = byPartialText("Analizar Imagen");

    public CapturePage(WebDriver driver) {
        super(driver);
        wait.until(ExpectedConditions.visibilityOfElementLocated(CAMERA_CARD));
    }

    // ── Queries ───────────────────────────────────────────────────────────────

    public boolean isCameraOptionVisible()        { return isPresent(CAMERA_CARD);    }
    public boolean isGalleryOptionVisible()       { return isPresent(GALLERY_CARD);   }
    public boolean isExplainabilityVisible()      { return isPresent(EXPLAINABILITY); }
    public boolean isFormatsInfoVisible()         { return isPresent(FORMATS_INFO);   }
    public boolean isPageHeaderVisible()          { return isPresent(PAGE_HEADER);    }
}
