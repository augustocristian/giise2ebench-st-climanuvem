package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.List;

/**
 * Page Object for profile configuration.
 */
public class ProfilePage extends BasePage {

    private static final By PROFILE_TITLE = anyText("My Profile");
    private static final By GUEST_PREFS = anyText("Guest preferences");
    private static final By USERNAME_SECTION = anyText("Username");
    private static final By DELETE_ACCOUNT = anyInteractiveText("Delete Account");
    private static final By CONFIRM_DELETE = anyInteractiveText("Yes, delete");
    private static final By CANCEL = anyInteractiveText("Cancel");
    private static final By ACCEPT = By.xpath("//*[@role='button' or self::button or @tabindex]"
            + "[contains(normalize-space(.),'Accept')"
            + " or contains(normalize-space(.),'OK')]");
    private static final By USERNAME_INPUT = By.cssSelector(
            "input[placeholder='Enter your name']");
    private static final By SAVE_BUTTON = anyInteractiveText("Save Changes");
    private static final By STATUS_FEEDBACK = By.xpath(
            "//*[contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    + "'abcdefghijklmnopqrstuvwxyz'), 'profile updated')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    + "'abcdefghijklmnopqrstuvwxyz'), 'security failure')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    + "'abcdefghijklmnopqrstuvwxyz'), 'error deleting data')"
                    + " or contains(translate(normalize-space(.),"
                    + "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    + "'abcdefghijklmnopqrstuvwxyz'), 'username must be between')]");

    public ProfilePage(WebDriver driver) {
        super(driver);
        wait.until(ExpectedConditions.visibilityOfElementLocated(PROFILE_TITLE));
    }

    public boolean isGuestPreferencesVisible() {
        return isVisible(GUEST_PREFS);
    }

    public ProfilePage waitForGuestProfile() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(GUEST_PREFS));
        return this;
    }

    public boolean isUsernameSectionVisible() {
        return isVisible(USERNAME_SECTION);
    }

    public ProfilePage waitForAuthenticatedProfile() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(USERNAME_SECTION));
        wait.until(ExpectedConditions.visibilityOfElementLocated(DELETE_ACCOUNT));
        return this;
    }

    public boolean isDeleteAccountVisible() {
        return isVisible(DELETE_ACCOUNT);
    }

    public boolean isDeleteConfirmVisible() {
        return isVisible(CONFIRM_DELETE);
    }

    public ProfilePage chooseLightTheme() {
        return chooseTheme("Light", "light");
    }

    public ProfilePage chooseDarkTheme() {
        return chooseTheme("Dark", "dark");
    }

    public ProfilePage chooseSystemTheme() {
        clickOption("System", false);
        waitForStoredValue("appTheme", "system");
        return this;
    }

    public ProfilePage chooseEnglishLanguage() {
        clickOption("English", false);
        waitForStoredValue("appLanguage", "en");
        return this;
    }

    public ProfilePage chooseSpanishLanguage() {
        clickOption("Spanish", false);
        waitForStoredValue("appLanguage", "es");
        return this;
    }

    public ProfilePage chooseSystemLanguage() {
        clickOption("System", true);
        waitForStoredValue("appLanguage", "system");
        return this;
    }

    public boolean hasStoredTheme(String value) {
        return value.equals(storedValue("appTheme"));
    }

    public boolean hasStoredLanguage(String value) {
        return value.equals(storedValue("appLanguage"));
    }

    public ProfilePage updateUsername(String username) {
        setUsername(username);
        click(SAVE_BUTTON);
        return this;
    }

    public ProfilePage setUsername(String username) {
        WebElement input = visibleUsernameInput();
        fillElement(input, username);
        return this;
    }

    public String currentUsername() {
        return visibleUsernameInput().getAttribute("value");
    }

    public boolean isSaveButtonEnabled() {
        WebElement button = wait.until(ExpectedConditions.visibilityOfElementLocated(SAVE_BUTTON));
        Object disabled = runScript(
                "var el = arguments[0];"
                        + "var target = el.closest('[role=\"button\"],button,[tabindex]') || el;"
                        + "return target.getAttribute('aria-disabled') === 'true'"
                        + " || target.disabled === true"
                        + " || window.getComputedStyle(target).pointerEvents === 'none';",
                button);
        return !(disabled instanceof Boolean && ((Boolean) disabled));
    }

    public ProfilePage waitForProfileFeedback() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(STATUS_FEEDBACK));
        return this;
    }

    public ProfilePage closeProfileFeedback() {
        click(ACCEPT);
        wait.until(webDriver -> !isPresent(STATUS_FEEDBACK));
        return this;
    }

    public ProfilePage openDeleteAccountDialog() {
        clickElement(lastVisible(DELETE_ACCOUNT));
        wait.until(ExpectedConditions.visibilityOfElementLocated(CONFIRM_DELETE));
        return this;
    }

    public ProfilePage cancelDeleteAccount() {
        click(CANCEL);
        wait.until(webDriver -> !isPresent(CONFIRM_DELETE));
        return this;
    }

    private ProfilePage chooseTheme(String label, String storedValue) {
        clickOption(label, false);
        waitForStoredValue("appTheme", storedValue);
        return this;
    }

    private void clickOption(String label, boolean lastMatch) {
        clickElement(wait.until(webDriver -> {
            List<WebElement> options = driver.findElements(anyInteractiveText(label));
            if (lastMatch) {
                for (int i = options.size() - 1; i >= 0; i--) {
                    WebElement option = options.get(i);
                    if (option.isDisplayed()) {
                        return option;
                    }
                }
            } else {
                for (WebElement option : options) {
                    if (option.isDisplayed()) {
                        return option;
                    }
                }
            }
            return null;
        }));
    }

    private void waitForStoredValue(String key, String expectedValue) {
        waitUntil(webDriver -> expectedValue.equals(storedValue(key)));
    }

    private WebElement visibleUsernameInput() {
        return wait.until(webDriver -> {
            List<WebElement> inputs = driver.findElements(USERNAME_INPUT);
            for (WebElement candidate : inputs) {
                if (candidate.isDisplayed()) {
                    return candidate;
                }
            }
            return null;
        });
    }

    private String storedValue(String key) {
        Object value = runScript("return window.localStorage.getItem(arguments[0]);", key);
        return value == null ? null : value.toString();
    }

    private WebElement lastVisible(By locator) {
        return wait.until(webDriver -> {
            List<WebElement> elements = driver.findElements(locator);
            for (int i = elements.size() - 1; i >= 0; i--) {
                WebElement element = elements.get(i);
                if (element.isDisplayed()) {
                    return element;
                }
            }
            return null;
        });
    }

    private static By anyText(String text) {
        return By.xpath("//*[contains(normalize-space(.),'" + text + "')]");
    }

    private static By anyInteractiveText(String text) {
        return By.xpath("//*[@role='button' or self::button or @tabindex]"
                + "[contains(normalize-space(.),'" + text + "')]");
    }
}
