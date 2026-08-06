package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.List;
import java.util.Set;

/**
 * Page Object for the Login form.
 * <p>
 * Constructing this object waits until the email input is visible.
 */
public class LoginPage extends BasePage {

    private static final By EMAIL_INPUT      = inputByPlaceholder("Correo electrónico");
    private static final By PASSWORD_INPUT   = inputByPlaceholder("Contraseña");
    private static final By FORGOT_PASSWORD  = byPartialText("Olvidaste tu contraseña");
    private static final By REGISTER_LINK    = byPartialText("Regístrate");
    private static final By SUBMIT_BUTTONS   = By.xpath(
            "//*[@role='button' or self::button or @tabindex]"
                    + "[contains(normalize-space(.),'Iniciar Sesión')]");
    private static final By GOOGLE_BUTTON    = byPartialText("Google");
    private static final By HOME_MARKER      = byPartialText("Bienvenido");
    private static final By LOGIN_FEEDBACK   = By.xpath(
            "//*[contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'error')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'incorrect')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'credencial')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'obligatorio')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'requerid')]");
    private static final By FEEDBACK_ACCEPT  = By.xpath(
            "//*[@role='button' or self::button or @tabindex]"
                    + "[contains(normalize-space(.),'Aceptar')"
                    + " or contains(normalize-space(.),'Accept')"
                    + " or contains(normalize-space(.),'OK')]");
    private final String frontendUrl;

    public LoginPage(WebDriver driver, String frontendUrl) {
        super(driver);
        this.frontendUrl = frontendUrl;
        wait.until(ExpectedConditions.visibilityOfElementLocated(EMAIL_INPUT));
    }

    // ── Queries ───────────────────────────────────────────────────────────────

    public boolean isEmailInputPresent()      { return isPresent(EMAIL_INPUT);     }
    public boolean isPasswordInputPresent()   { return isPresent(PASSWORD_INPUT);  }
    public boolean isForgotPasswordPresent()  { return isPresent(FORGOT_PASSWORD); }
    public boolean isRegisterLinkPresent()    { return isPresent(REGISTER_LINK);   }
    public boolean isGoogleLoginPresent()     { return isPresent(GOOGLE_BUTTON);    }
    public boolean isHomeVisible()            { return isPresent(HOME_MARKER);      }
    public String  getEmailValue()            { return inputValue(EMAIL_INPUT);     }

    public boolean hasLoginErrorOrValidation() {
        return isVisible(LOGIN_FEEDBACK) || hasInvalidRequiredInput();
    }

    // ── Actions ───────────────────────────────────────────────────────────────

    /** Types into the email field. Returns {@code this} for fluent chaining. */
    public LoginPage enterEmail(String email) {
        fill(EMAIL_INPUT, email);
        return this;
    }

    /** Types into the password field. Returns {@code this} for fluent chaining. */
    public LoginPage enterPassword(String password) {
        fill(PASSWORD_INPUT, password);
        return this;
    }

    /** Submits the email/password login form and stays on the current page object. */
    public LoginPage submitLogin() {
        clickElement(lastVisibleSubmitButton());
        return this;
    }

    /** Fills both fields and submits the email/password login form. */
    public LoginPage login(String email, String password) {
        waitForLoginFormReady();
        enterEmail(email);
        enterPassword(password);
        return submitLogin();
    }

    /** Waits until the authenticated Home screen is visible and returns its page object. */
    public HomePage waitForHome() {
        try {
            waitUntil(webDriver -> isVisible(HOME_MARKER) || hasLoginErrorOrValidation());
        } catch (TimeoutException e) {
            throw new AssertionError("Login did not reach Home before timeout. Check account credentials in ACCOUNTS_FILE.", e);
        }
        if (hasLoginErrorOrValidation() && !isVisible(HOME_MARKER)) {
            throw new AssertionError("Login failed before reaching Home. Check account credentials in ACCOUNTS_FILE.");
        }
        return new HomePage(driver, frontendUrl);
    }

    /** Waits until the login attempt is rejected by UI validation or an error message. */
    public LoginPage waitForLoginFailure() {
        waitUntil(webDriver -> hasLoginErrorOrValidation() && isEmailInputPresent());
        return this;
    }

    public LoginPage closeLoginFeedbackIfPresent() {
        List<WebElement> buttons = driver.findElements(FEEDBACK_ACCEPT);
        for (int i = buttons.size() - 1; i >= 0; i--) {
            WebElement button = buttons.get(i);
            if (button.isDisplayed()) {
                clickElement(button);
                break;
            }
        }
        return this;
    }

    private void waitForLoginFormReady() {
        waitUntil(webDriver -> inputIsEditable(EMAIL_INPUT) && inputIsEditable(PASSWORD_INPUT));
    }

    /**
     * Starts the Google provider flow without requiring credentials. The flow is
     * considered started when a provider window/tab opens or the current page URL
     * or body contains a Google/Firebase identity marker.
     */
    public boolean clickGoogleLoginStartsProvider() {
        Set<String> originalWindows = driver.getWindowHandles();
        click(GOOGLE_BUTTON);
        return waitUntil(webDriver -> driver.getWindowHandles().size() > originalWindows.size()
                || containsIdentityProviderMarker());
    }

    /** Clicks "¿No tienes cuenta? Regístrate" and waits for the Register form. */
    public RegisterPage clickRegisterLink() {
        click(REGISTER_LINK);
        return new RegisterPage(driver, frontendUrl);
    }

    private boolean containsIdentityProviderMarker() {
        String url = driver.getCurrentUrl().toLowerCase();
        String body = driver.findElement(By.tagName("body")).getText().toLowerCase();
        return url.contains("google") || url.contains("firebase") || url.contains("identitytoolkit")
                || body.contains("google") || body.contains("firebase");
    }

    private boolean inputIsEditable(By locator) {
        List<WebElement> inputs = driver.findElements(locator);
        for (WebElement input : inputs) {
            if (input.isDisplayed() && input.isEnabled()) {
                Object readOnly = runScript("return arguments[0].readOnly === true;", input);
                return !(readOnly instanceof Boolean && ((Boolean) readOnly));
            }
        }
        return false;
    }

    private WebElement lastVisibleSubmitButton() {
        return wait.until(webDriver -> {
            List<WebElement> buttons = driver.findElements(SUBMIT_BUTTONS);
            for (int i = buttons.size() - 1; i >= 0; i--) {
                WebElement button = buttons.get(i);
                if (button.isDisplayed()) {
                    return button;
                }
            }
            return null;
        });
    }
}
