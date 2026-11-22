package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.List;

/**
 * Page Object for the Register form.
 * <p>
 * Constructing this object waits until the username input is visible.
 */
public class RegisterPage extends BasePage {

    private static final By USERNAME_INPUT         = inputByPlaceholder("Nombre de usuario");
    private static final By EMAIL_INPUT            = inputByPlaceholder("Correo electrónico");
    private static final By PASSWORD_INPUT         = inputByPlaceholder("Contraseña");
    private static final By CONFIRM_PASSWORD_INPUT = inputByPlaceholder("Confirmar contraseña");
    private static final By ALL_INPUTS             = By.cssSelector("input");
    private static final By LOGIN_LINK             = byPartialText("Inicia sesión");
    private static final By SUBMIT_BUTTONS         = By.xpath(
            "//*[@role='button' or self::button or @tabindex]"
                    + "[contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'registr')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'crear')]");
    private static final By HOME_MARKER            = byPartialText("Bienvenido");
    private static final By VERIFY_EMAIL_DIALOG    = By.xpath(
            "//*[contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'verific')"
                    + " and contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'correo')]");
    private static final By REGISTER_FEEDBACK      = By.xpath(
            "//*[contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'error')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'inválid')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'invalid')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'contraseña')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'correo')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'usuario')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'coincid')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'uso')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'obligatorio')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ',"
                    + "'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), 'requerid')]");
    private final String frontendUrl;

    public RegisterPage(WebDriver driver, String frontendUrl) {
        super(driver);
        this.frontendUrl = frontendUrl;
        wait.until(ExpectedConditions.visibilityOfElementLocated(USERNAME_INPUT));
    }

    // ── Queries ───────────────────────────────────────────────────────────────

    public boolean isUsernameInputPresent()        { return isPresent(USERNAME_INPUT) || visibleInputCount() >= 1; }
    public boolean isEmailInputPresent()           { return isPresent(EMAIL_INPUT) || visibleInputCount() >= 2; }
    public boolean isPasswordInputPresent()        { return isPresent(PASSWORD_INPUT) || visibleInputCount() >= 3; }
    public boolean isConfirmPasswordInputPresent() { return isPresent(CONFIRM_PASSWORD_INPUT) || visibleInputCount() >= 4; }
    public boolean isLoginLinkPresent()            { return isPresent(LOGIN_LINK);             }
    public boolean isHomeVisible()                 { return isPresent(HOME_MARKER);            }
    public boolean isVerificationDialogVisible()   { return isVisible(VERIFY_EMAIL_DIALOG);    }

    public boolean hasRegisterErrorOrValidation() {
        return isVisible(REGISTER_FEEDBACK) || hasInvalidRequiredInput();
    }

    // ── Actions ───────────────────────────────────────────────────────────────

    public RegisterPage enterUsername(String username) {
        fillElement(inputAt(0, USERNAME_INPUT), username);
        return this;
    }

    public RegisterPage enterEmail(String email) {
        fillElement(inputAt(1, EMAIL_INPUT), email);
        return this;
    }

    public RegisterPage enterPassword(String password) {
        fillElement(inputAt(2, PASSWORD_INPUT), password);
        return this;
    }

    public RegisterPage enterConfirmPassword(String password) {
        fillElement(inputAt(3, CONFIRM_PASSWORD_INPUT), password);
        return this;
    }

    public RegisterPage submitRegister() {
        clickElement(lastVisibleSubmitButton());
        return this;
    }

    public RegisterPage register(String username, String email, String password, String confirmPassword) {
        enterUsername(username);
        enterEmail(email);
        enterPassword(password);
        enterConfirmPassword(confirmPassword);
        return submitRegister();
    }

    public HomePage waitForHome() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(HOME_MARKER));
        return new HomePage(driver, frontendUrl);
    }

    public RegisterPage waitForVerificationDialog() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(VERIFY_EMAIL_DIALOG));
        return this;
    }

    public RegisterPage waitForRegisterFailure() {
        waitUntil(webDriver -> hasRegisterErrorOrValidation() && isUsernameInputPresent());
        return this;
    }

    /** Navigates back to the Login form. */
    public LoginPage clickLoginLink() {
        click(LOGIN_LINK);
        return new LoginPage(driver, frontendUrl);
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

    private WebElement inputAt(int index, By preferredLocator) {
        return wait.until(webDriver -> {
            List<WebElement> preferred = driver.findElements(preferredLocator);
            for (WebElement input : preferred) {
                if (input.isDisplayed()) {
                    return input;
                }
            }

            List<WebElement> visibleInputs = visibleInputs();
            return visibleInputs.size() > index ? visibleInputs.get(index) : null;
        });
    }

    private int visibleInputCount() {
        return visibleInputs().size();
    }

    private List<WebElement> visibleInputs() {
        List<WebElement> inputs = driver.findElements(ALL_INPUTS);
        inputs.removeIf(input -> !input.isDisplayed());
        return inputs;
    }
}
