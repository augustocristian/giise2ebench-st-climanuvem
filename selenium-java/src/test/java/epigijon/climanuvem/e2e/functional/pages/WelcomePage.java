package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;

/**
 * Page Object for the Welcome (root) screen — the first page any visitor sees.
 * <p>
 * Constructing this object waits until the anonymous-login button is visible,
 * which guarantees the React bundle has fully mounted before any assertion runs.
 */
public class WelcomePage extends BasePage {

    private static final By GUEST_BUTTON  = byPartialText("Continuar como invitado");
    private static final By LOGIN_BUTTON  = byPartialText("Iniciar Sesión");
    private static final By APP_TITLE     = byPartialText("ClimaNuvem");
    private static final By TAGLINE       = byPartialText("Meteorólogo de bolsillo");
    private final String frontendUrl;

    public WelcomePage(WebDriver driver, String frontendUrl) {
        super(driver);
        this.frontendUrl = frontendUrl;
        wait.until(ExpectedConditions.visibilityOfElementLocated(GUEST_BUTTON));
    }

    // ── Queries ───────────────────────────────────────────────────────────────

    public boolean isAppTitleVisible()        { return isPresent(APP_TITLE);    }
    public boolean isTaglineVisible()         { return isPresent(TAGLINE);      }
    public boolean isLoginButtonPresent()     { return isPresent(LOGIN_BUTTON); }
    public boolean isGuestButtonPresent()     { return isPresent(GUEST_BUTTON); }
    public boolean isHomeVisible()            { return isPresent(byPartialText("Bienvenido")); }

    // ── Actions ───────────────────────────────────────────────────────────────

    /** Clicks "Iniciar Sesión" and waits for the Login form to appear. */
    public LoginPage clickLoginButton() {
        click(LOGIN_BUTTON);
        return new LoginPage(driver, frontendUrl);
    }

    /**
     * Clicks "Continuar como invitado", which triggers Firebase anonymous auth,
     * and waits for the Home screen to mount.
     */
    public HomePage clickAnonymousLogin() {
        click(GUEST_BUTTON);
        return new HomePage(driver, frontendUrl);
    }
}
