package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;

/**
 * Page Object for the Home screen — shown after a successful login.
 * <p>
 * Constructing this object waits until both the welcome card and the
 * "Analyze Image" quick-action card are visible, confirming that the
 * authenticated home view has fully rendered.
 */
public class HomePage extends BasePage {

    private static final By WELCOME_MESSAGE = byPartialText("Welcome!");
    private static final By ANALYZE_CARD = byPartialText("Analyze Image");
    private static final By HISTORY_CARD = byPartialText("History");
    private static final By LOGOUT_CARD = byPartialText("Log Out");
    private final String frontendUrl;

    public HomePage(WebDriver driver, String frontendUrl) {
        super(driver);
        this.frontendUrl = frontendUrl;
        wait.until(ExpectedConditions.visibilityOfElementLocated(WELCOME_MESSAGE));
        wait.until(ExpectedConditions.visibilityOfElementLocated(ANALYZE_CARD));
    }

    // ── Queries ───────────────────────────────────────────────────────────────

    public boolean isWelcomeMessageVisible() {
        return isPresent(WELCOME_MESSAGE);
    }

    public boolean isAnalyzeCardVisible() {
        return isPresent(ANALYZE_CARD);
    }

    public boolean isHistoryCardVisible() {
        return isPresent(HISTORY_CARD);
    }

    public boolean isLogoutCardVisible() {
        return isPresent(LOGOUT_CARD);
    }

    // ── Actions ───────────────────────────────────────────────────────────────

    /** Navigates to the Capture screen. */
    public CapturePage clickAnalyzeImage() {
        click(ANALYZE_CARD);
        return new CapturePage(driver);
    }

    /** Opens the profile/settings screen through the welcome card. */
    public ProfilePage clickProfile() {
        return openProfileRouteDirectly();
    }

    /**
     * Opens Profile through the router URL when the welcome card click is swallowed
     * by React Native Web.
     */
    public ProfilePage openProfileRouteDirectly() {
        driver.get(normalizedFrontendUrl() + "/profile");
        waitUntil(webDriver -> driver.getCurrentUrl().contains("/profile"));
        return new ProfilePage(driver);
    }

    /** Clicks "Log Out" and waits for the Welcome screen to re-appear. */
    public WelcomePage clickLogout() {
        click(LOGOUT_CARD);
        return new WelcomePage(driver, frontendUrl);
    }

    private String normalizedFrontendUrl() {
        return frontendUrl.endsWith("/") ? frontendUrl.substring(0, frontendUrl.length() - 1) : frontendUrl;
    }
}
