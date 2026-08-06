package epigijon.climanuvem.e2e.functional.common;

import epigijon.climanuvem.e2e.functional.pages.HomePage;
import epigijon.climanuvem.e2e.functional.pages.LoginPage;
import epigijon.climanuvem.e2e.functional.pages.WelcomePage;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Properties;
import java.util.stream.Stream;

/**
 * Base class for the ClimaNuvem browser system tests.
 * <p>
 * Manages the Chrome WebDriver lifecycle: a fresh session is created before
 * each test and closed afterward, preventing any state leakage between tests.
 * <p>
 * Entry points for test methods:
 * <ul>
 *   <li>{@link #onWelcomePage()} — navigates to the root URL and returns a
 *       {@link WelcomePage}, which waits internally until the page is ready.</li>
 *   <li>{@link #loginAsGuest()} — convenience shortcut that clicks
 *       "Continuar como invitado" and returns a {@link HomePage}.</li>
 * </ul>
 * <p>
 * Set {@code -DCI=true} (or the {@code CI} env var) for headless Chrome in CI.
 * Override browser and accounts-file values via {@code -D...} system
 * properties, matching environment variables, or {@code test.properties}.
 */
@SuppressWarnings("java:S5786") // must be public — subclasses live in a different package
public class BaseLoggedClass {

    protected static final Logger log = LoggerFactory.getLogger(BaseLoggedClass.class);

    protected static String frontendUrl;
    protected static String accountsFile;
    protected static TestAccounts testAccounts;
    protected static String firebaseWebApiKey;
    protected static String registerEmailDomain;

    protected WebDriver driver;

    @BeforeAll
    static void setUpClass() throws IOException {
        Properties props = new Properties();
        props.load(Files.newInputStream(Paths.get("src/test/resources/test.properties")));

        frontendUrl = configuredValue(props, "FRONTEND_URL", "http://localhost:5173");
        accountsFile = configuredValue(props, "ACCOUNTS_FILE", "src/test/resources/accounts.local.csv");
        try {
            testAccounts = TestAccounts.load(accountsFile);
        } catch (IOException | RuntimeException e) {
            log.warn("Could not load system-test accounts from {}. Tests that require accounts will fail only when "
                    + "they request one.", accountsFile, e);
            testAccounts = TestAccounts.empty();
        }
        firebaseWebApiKey = configuredValue(props, "FIREBASE_WEB_API_KEY", "");
        registerEmailDomain = configuredValue(props, "REGISTER_EMAIL_DOMAIN", "example.test");

        log.info("Frontend URL: {}", frontendUrl);
        log.info("System-test accounts file: {}", accountsFile);
    }

    @BeforeEach
    void setUpTest() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--incognito", "--disable-blink-features=AutomationControlled");
        if (isHeadless()) {
            options.addArguments("--headless=new", "--no-sandbox", "--disable-dev-shm-usage");
        }

        driver = new ChromeDriver(options);
        driver.manage().window().maximize();
        log.info("Browser started");
    }

    @AfterEach
    void tearDownTest() {
        if (driver != null) {
            driver.quit();
            log.info("Browser closed");
        }
    }

    /**
     * Navigates to the frontend root and returns a {@link WelcomePage}.
     * The page object waits internally until the Welcome screen is ready.
     */
    protected WelcomePage onWelcomePage() {
        driver.get(frontendUrl);
        return new WelcomePage(driver, frontendUrl);
    }

    /**
     * Clicks "Continuar como invitado" on the Welcome screen and returns a
     * {@link HomePage} once the Home screen has finished loading.
     * Firebase anonymous auth is invoked; the backend accepts the resulting
     * token because {@code TEST_MODE=true} accepts any Bearer token.
     */
    protected HomePage loginAsGuest() {
        return onWelcomePage().clickAnonymousLogin();
    }

    protected HomePage loginAsProfileUser() {
        TestAccount account = profileAccount();

        LoginPage loginPage = onWelcomePage()
                .clickLoginButton()
                .login(account.getEmail(), account.getPassword());
        return loginPage.waitForHome();
    }

    protected static Stream<TestAccount> loginAccounts() {
        List<TestAccount> accounts = testAccounts.byRole(TestAccounts.ROLE_LOGIN_USER);
        if (accounts.isEmpty()) {
            throw new AssertionError("Configure at least one login_user in " + accountsFile + ".");
        }
        return accounts.stream();
    }

    protected static Stream<TestAccount> profileAccounts() {
        List<TestAccount> accounts = testAccounts.byRole(TestAccounts.ROLE_PROFILE_USER);
        if (accounts.isEmpty()) {
            throw new AssertionError("Configure at least one profile_user in " + accountsFile + ".");
        }
        return accounts.stream();
    }

    protected static TestAccount loginAccount() {
        return testAccounts.requiredSingle(TestAccounts.ROLE_LOGIN_USER);
    }

    protected static TestAccount profileAccount() {
        return testAccounts.requiredSingle(TestAccounts.ROLE_PROFILE_USER);
    }

    protected static TestAccount unknownAccount() {
        return testAccounts.requiredSingle(TestAccounts.ROLE_UNKNOWN_USER);
    }

    protected void deleteFirebaseAccountIfConfigured(String email, String password) {
        if (firebaseWebApiKey == null || firebaseWebApiKey.trim().isEmpty()) {
            log.warn("Skipping Firebase account cleanup for {} because FIREBASE_WEB_API_KEY is not configured", email);
            return;
        }

        try {
            JsonObject signInRequest = new JsonObject();
            signInRequest.addProperty("email", email);
            signInRequest.addProperty("password", password);
            signInRequest.addProperty("returnSecureToken", true);
            String signInResponse = postFirebaseAuth("accounts:signInWithPassword", signInRequest.toString());
            JsonObject signInJson = JsonParser.parseString(signInResponse).getAsJsonObject();
            String idToken = signInJson.get("idToken").getAsString();

            JsonObject deleteRequest = new JsonObject();
            deleteRequest.addProperty("idToken", idToken);
            postFirebaseAuth("accounts:delete", deleteRequest.toString());
            log.info("Deleted Firebase account created during test: {}", email);
        } catch (Exception e) {
            log.warn("Could not delete Firebase account created during test: {}", email, e);
        }
    }

    private static String configuredValue(Properties props, String key, String fallback) {
        String systemValue = System.getProperty(key);
        if (systemValue != null) {
            return systemValue;
        }
        String envValue = System.getenv(key);
        if (envValue != null) {
            return envValue;
        }
        return props.getProperty(key, fallback);
    }

    private String postFirebaseAuth(String method, String body) throws IOException {
        URL url = new URL("https://identitytoolkit.googleapis.com/v1/" + method + "?key=" + firebaseWebApiKey);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            os.write(body.getBytes(StandardCharsets.UTF_8));
        }

        int status = connection.getResponseCode();
        java.io.InputStream responseStream = status >= 200 && status < 300
                ? connection.getInputStream()
                : connection.getErrorStream();
        String response = new String(responseStream.readAllBytes(), StandardCharsets.UTF_8);
        if (status < 200 || status >= 300) {
            throw new IOException("Firebase Auth request failed with HTTP " + status + ": " + response);
        }
        return response;
    }

    private boolean isHeadless() {
        return "true".equalsIgnoreCase(System.getProperty("CI"))
                || "true".equalsIgnoreCase(System.getenv("CI"));
    }
}
