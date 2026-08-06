package epigijon.climanuvem.e2e.functional.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.WebDriverException;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

/**
 * Abstract base for all Page Objects.
 * <p>
 * Centralises the WebDriver, a shared explicit wait, and the three primitives
 * every page needs — {@link #isPresent}, {@link #click}, and {@link #fill}.
 * Subclasses declare their own locators as private static constants and expose
 * typed, readable methods that either return a boolean/value or the next page.
 */
abstract class BasePage {

    static final int TIMEOUT_SECONDS = 30;

    protected final WebDriver driver;
    protected final WebDriverWait wait;

    protected BasePage(WebDriver driver) {
        this.driver = driver;
        this.wait   = new WebDriverWait(driver, Duration.ofSeconds(TIMEOUT_SECONDS));
    }

    /** True when at least one element matching {@code locator} exists in the DOM. */
    protected boolean isPresent(By locator) {
        return !driver.findElements(locator).isEmpty();
    }

    /** Waits for {@code locator} to be clickable and clicks it. */
    protected void click(By locator) {
        WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
        clickElement(el);
    }

    /** Clicks an already located element using the React Native Web event chain. */
    protected void clickElement(WebElement el) {
        ((JavascriptExecutor) driver).executeScript(
                "var el = arguments[0];"
                        + "var target = el.closest('[role=\"button\"],[role=\"link\"],button,a,[tabindex]') || el;"
                        + "target.scrollIntoView({block: 'center', inline: 'center'});"
                        + "['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(type) {"
                        + "  target.dispatchEvent(new MouseEvent(type, {bubbles: true, cancelable: true, view: window}));"
                        + "});",
                el);
    }

    /** Waits for {@code locator} to be visible, clears it, and types {@code text}. */
    protected void fill(By locator, String text) {
        WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
        fillElement(el, text);
    }

    /** Clears and types into an already located input element. */
    protected void fillElement(WebElement el, String text) {
        try {
            el.clear();
            el.sendKeys(text);
        } catch (WebDriverException e) {
            setInputValue(el, text);
        }
    }

    /** Returns the current {@code value} attribute of an input element. */
    protected String inputValue(By locator) {
        return driver.findElement(locator).getAttribute("value");
    }

    /** True when any element matching {@code locator} is currently visible. */
    protected boolean isVisible(By locator) {
        return driver.findElements(locator).stream().anyMatch(WebElement::isDisplayed);
    }

    /** Waits until the supplied condition returns true. */
    protected boolean waitUntil(ExpectedCondition<Boolean> condition) {
        return wait.until(condition);
    }

    /** Runs JavaScript and returns its raw value. */
    protected Object runScript(String script, Object... args) {
        return ((JavascriptExecutor) driver).executeScript(script, args);
    }

    /** Sets an input value through the native property setter and notifies React. */
    protected void setInputValue(WebElement el, String text) {
        runScript(
                "var el = arguments[0];"
                        + "var value = arguments[1];"
                        + "var setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set;"
                        + "setter.call(el, value);"
                        + "el.dispatchEvent(new Event('input', {bubbles: true}));"
                        + "el.dispatchEvent(new Event('change', {bubbles: true}));",
                el, text);
    }

    /** True when any required input currently fails browser-side validation. */
    protected boolean hasInvalidRequiredInput() {
        Object invalidCount = runScript(
                "return Array.from(document.querySelectorAll('input'))"
                        + ".filter(function(input) { return input.required && !input.checkValidity(); }).length;");
        return invalidCount instanceof Number && ((Number) invalidCount).intValue() > 0;
    }

    // ── Shared locator factories ──────────────────────────────────────────────

    /** XPath: any element whose full text equals {@code text}. */
    protected static By byText(String text) {
        return By.xpath("//*[normalize-space(.)='" + text + "' and not(.//*[normalize-space(.)='" + text + "'])]");
    }

    /** XPath: any element whose text contains {@code text} as a substring. */
    protected static By byPartialText(String text) {
        return By.xpath("//*[contains(normalize-space(.),'" + text + "') and not(.//*[contains(normalize-space(.),'" + text + "')])]");
    }

    /** CSS: {@code <input>} with the given placeholder. */
    protected static By inputByPlaceholder(String placeholder) {
        return By.cssSelector("input[placeholder='" + placeholder + "']");
    }
}
