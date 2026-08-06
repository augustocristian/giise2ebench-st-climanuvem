package epigijon.climanuvem.e2e.functional.common;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.apache.http.HttpEntity;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPatch;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.entity.mime.content.ByteArrayBody;
import org.apache.http.entity.mime.content.StringBody;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Properties;

/**
 * Base class for the ClimaNuvem API test suite. Handles HTTP plumbing, Firebase
 * auth-token injection, multipart image upload, and common fixture creation.
 * <p>
 * The SUT must be started in TEST_MODE=true so that requests bearing
 * {@code testToken}
 * bypass Firebase verification. Use {@code deploy-local.sh} /
 * {@code deploy-local.ps1}
 * to bring up the test environment before running the suite.
 */
public class BaseApiClass {

    protected static final Logger log = LoggerFactory.getLogger(BaseApiClass.class);

    protected static CloseableHttpClient httpClient;
    protected static String sutUrl;
    protected static String testToken;
    protected static Properties properties;
    protected static String tJobName;
    private static int httpTimeoutMs;

    protected static class ApiResponse {
        private final int statusCode;
        private final String body;

        ApiResponse(int statusCode, String body) {
            this.statusCode = statusCode;
            this.body = body;
        }

        public int getStatusCode() {
            return statusCode;
        }

        public String getBody() {
            return body;
        }
    }

    @BeforeAll
    static void setupAll() throws IOException {
        log.info("Starting ClimaNuvem API test global setup");
        properties = new Properties();
        properties.load(Files.newInputStream(Paths.get("src/test/resources/test.properties")));
        tJobName = System.getProperty("TJOB_NAME");

        String envUrl = System.getProperty("SUT_URL") != null
                ? System.getProperty("SUT_URL")
                : System.getenv("SUT_URL");
        sutUrl = envUrl != null ? envUrl : properties.getProperty("LOCALHOST_URL");

        String envToken = System.getProperty("TEST_TOKEN") != null
                ? System.getProperty("TEST_TOKEN")
                : System.getenv("TEST_TOKEN");
        testToken = envToken != null ? envToken : properties.getProperty("TEST_TOKEN");
        httpTimeoutMs = Integer.parseInt(configuredValue("HTTP_TIMEOUT_MS", "10000"));

        log.info("API base URL: {}", sutUrl);
        log.info("HTTP timeout: {} ms", httpTimeoutMs);
        RequestConfig requestConfig = RequestConfig.custom()
                .setConnectTimeout(httpTimeoutMs)
                .setConnectionRequestTimeout(httpTimeoutMs)
                .setSocketTimeout(httpTimeoutMs)
                .build();
        httpClient = HttpClients.custom()
                .setDefaultRequestConfig(requestConfig)
                .build();
    }

    @AfterAll
    static void tearDownAll() throws IOException {
        if (httpClient != null) {
            httpClient.close();
            log.info("Shared HTTP client closed");
        }
    }

    // ── URL builders ─────────────────────────────────────────────────────────

    protected String analysisUrl(String path) {
        return sutUrl + "/analysis" + path;
    }

    protected String rootUrl(String path) {
        return sutUrl + path;
    }

    // ── Unauthenticated HTTP ─────────────────────────────────────────────────

    protected String get(String url) throws IOException {
        HttpGet request = new HttpGet(url);
        request.addHeader("Accept", "application/json");
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity entity = response.getEntity();
            String body = entity != null ? EntityUtils.toString(entity) : "";
            log.debug("GET {} -> {} ({} chars)", url, response.getStatusLine().getStatusCode(), body.length());
            return body;
        }
    }

    protected int getStatus(String url) throws IOException {
        return statusOf(new HttpGet(url));
    }

    // ── Authenticated HTTP ───────────────────────────────────────────────────

    protected String getAuth(String url) throws IOException {
        HttpGet request = new HttpGet(url);
        request.addHeader("Accept", "application/json");
        request.addHeader("Authorization", "Bearer " + testToken);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity entity = response.getEntity();
            String body = entity != null ? EntityUtils.toString(entity) : "";
            log.debug("GET(auth) {} -> {} ({} chars)", url, response.getStatusLine().getStatusCode(), body.length());
            return body;
        }
    }

    protected int getStatusAuth(String url) throws IOException {
        HttpGet request = new HttpGet(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        return statusOf(request);
    }

    protected int deleteStatusAuth(String url) throws IOException {
        HttpDelete request = new HttpDelete(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        return statusOf(request);
    }

    protected int patchStatusAuth(String url) throws IOException {
        HttpPatch request = new HttpPatch(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        return statusOf(request);
    }

    // ── Multipart image upload ────────────────────────────────────────────────

    protected String uploadImage(String url, byte[] imageBytes, String location) throws IOException {
        HttpPost request = new HttpPost(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        HttpEntity entity = MultipartEntityBuilder.create()
                .addPart("file", new ByteArrayBody(imageBytes, ContentType.IMAGE_JPEG, "test.jpg"))
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN))
                .build();
        request.setEntity(entity);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            String body = responseEntity != null ? EntityUtils.toString(responseEntity) : "";
            log.debug("POST(upload) {} -> {} ({} chars)", url, response.getStatusLine().getStatusCode(), body.length());
            return body;
        }
    }

    protected int uploadImageStatus(String url, byte[] imageBytes, String location) throws IOException {
        HttpPost request = new HttpPost(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        HttpEntity entity = MultipartEntityBuilder.create()
                .addPart("file", new ByteArrayBody(imageBytes, ContentType.IMAGE_JPEG, "test.jpg"))
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN))
                .build();
        request.setEntity(entity);
        return statusOf(request);
    }

    protected String uploadImage(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        return uploadImageResponse(url, imageBytes, filename, contentType, location, includeExplainability).getBody();
    }

    protected ApiResponse uploadImageResponse(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        HttpPost request = new HttpPost(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        HttpEntity entity = MultipartEntityBuilder.create()
                .addPart("file", new ByteArrayBody(imageBytes, contentType, filename))
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN))
                .addPart("include_explainability", new StringBody(String.valueOf(includeExplainability),
                        ContentType.TEXT_PLAIN))
                .build();
        request.setEntity(entity);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            String body = responseEntity != null ? EntityUtils.toString(responseEntity) : "";
            log.debug("POST(upload) {} -> {} ({} chars)", url, response.getStatusLine().getStatusCode(), body.length());
            return new ApiResponse(response.getStatusLine().getStatusCode(), body);
        }
    }

    protected int uploadImageStatus(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        HttpPost request = new HttpPost(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        HttpEntity entity = MultipartEntityBuilder.create()
                .addPart("file", new ByteArrayBody(imageBytes, contentType, filename))
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN))
                .addPart("include_explainability", new StringBody(String.valueOf(includeExplainability),
                        ContentType.TEXT_PLAIN))
                .build();
        request.setEntity(entity);
        return statusOf(request);
    }

    protected int uploadWithoutFileStatus(String url, String location) throws IOException {
        HttpPost request = new HttpPost(url);
        request.addHeader("Authorization", "Bearer " + testToken);
        HttpEntity entity = MultipartEntityBuilder.create()
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN))
                .build();
        request.setEntity(entity);
        return statusOf(request);
    }

    private int statusOf(HttpUriRequest request) throws IOException {
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            EntityUtils.consumeQuietly(response.getEntity());
            int status = response.getStatusLine().getStatusCode();
            log.debug("{} {} -> {}", request.getMethod(), request.getURI(), status);
            return status;
        }
    }

    // ── JSON helpers ──────────────────────────────────────────────────────────

    protected JsonObject getJsonObject(String url) throws IOException {
        return JsonParser.parseString(get(url)).getAsJsonObject();
    }

    protected JsonObject getJsonObjectAuth(String url) throws IOException {
        return JsonParser.parseString(getAuth(url)).getAsJsonObject();
    }

    protected JsonArray getJsonArrayAuth(String url) throws IOException {
        return JsonParser.parseString(getAuth(url)).getAsJsonArray();
    }

    protected JsonObject findAnalysisInHistory(int analysisId) throws IOException {
        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        for (JsonElement element : history) {
            if (element.isJsonObject()) {
                JsonObject object = element.getAsJsonObject();
                if (object.has("id") && object.get("id").getAsInt() == analysisId) {
                    return object;
                }
            }
        }
        return null;
    }

    protected JsonObject waitForAnalysisTerminalStatus(int analysisId, long timeoutMillis, long pollMillis)
            throws IOException {
        long deadline = System.currentTimeMillis() + timeoutMillis;
        JsonObject lastSeen = null;

        while (System.currentTimeMillis() < deadline) {
            lastSeen = findAnalysisInHistory(analysisId);
            if (lastSeen != null && lastSeen.has("status")) {
                String status = lastSeen.get("status").getAsString();
                if ("completed".equals(status) || "cancelled".equals(status)) {
                    return lastSeen;
                }
            }
            sleepQuietly(pollMillis);
        }

        return lastSeen;
    }

    protected static boolean containsByField(JsonArray array, String fieldName, String expected) {
        for (JsonElement element : array) {
            if (element.isJsonObject()
                    && expected.equals(element.getAsJsonObject().get(fieldName).getAsString())) {
                return true;
            }
        }
        return false;
    }

    // ── Test data helpers ─────────────────────────────────────────────────────

    protected static long unique() {
        return System.currentTimeMillis();
    }

    /**
     * Creates a minimal 10x10 JPEG in memory — small enough to be fast, valid
     * enough for the
     * upload endpoint to accept (it only needs a readable byte stream).
     */
    protected static byte[] createTestImage() throws IOException {
        BufferedImage img = new BufferedImage(10, 10, BufferedImage.TYPE_INT_RGB);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(img, "jpg", baos);
        return baos.toByteArray();
    }

    protected static byte[] createCloudyJpeg() throws IOException {
        BufferedImage img = new BufferedImage(640, 360, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = img.createGraphics();
        try {
            graphics.setColor(new Color(98, 171, 232));
            graphics.fillRect(0, 0, img.getWidth(), img.getHeight());
            graphics.setColor(new Color(245, 248, 250));
            graphics.fillOval(120, 95, 180, 95);
            graphics.fillOval(235, 70, 210, 125);
            graphics.fillOval(380, 115, 150, 80);
            graphics.fillRect(175, 145, 310, 75);
            graphics.setColor(new Color(225, 232, 238));
            graphics.fillOval(210, 175, 170, 55);
        } finally {
            graphics.dispose();
        }
        return writeJpeg(img);
    }

    protected static byte[] createNoCloudJpeg() throws IOException {
        BufferedImage img = new BufferedImage(640, 360, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = img.createGraphics();
        try {
            for (int y = 0; y < img.getHeight(); y++) {
                float ratio = (float) y / (float) img.getHeight();
                int red = 70 + Math.round(35 * ratio);
                int green = 155 + Math.round(45 * ratio);
                int blue = 225 + Math.round(25 * ratio);
                graphics.setColor(new Color(red, green, blue));
                graphics.drawLine(0, y, img.getWidth(), y);
            }
        } finally {
            graphics.dispose();
        }
        return writeJpeg(img);
    }

    protected static byte[] createEmptyImageBytes() {
        return new byte[0];
    }

    protected static byte[] createTooLargePayload() throws IOException {
        byte[] payload = new byte[(5 * 1024 * 1024) + 1];
        byte[] validJpeg = createTestImage();
        System.arraycopy(validJpeg, 0, payload, 0, validJpeg.length);
        for (int i = validJpeg.length; i < payload.length; i++) {
            payload[i] = (byte) (i % 251);
        }
        return payload;
    }

    protected static byte[] createNonJpegPayload() {
        return "not-a-jpeg-image".getBytes(java.nio.charset.StandardCharsets.UTF_8);
    }

    /**
     * Uploads a test image to {@code POST /analysis/upload} and returns the
     * assigned analysis ID.
     */
    protected int createAnalysis(String location) throws IOException {
        byte[] img = createTestImage();
        String response = uploadImage(analysisUrl("/upload"), img, location);
        return JsonParser.parseString(response).getAsJsonObject().get("analysis_id").getAsInt();
    }

    /**
     * Deletes all analysis records for the test user via
     * {@code DELETE /analysis/user-data}.
     * Call this in {@code @BeforeAll} for tests that require an empty history.
     */
    protected void deleteAllUserData() throws IOException {
        deleteStatusAuth(analysisUrl("/user-data"));
        log.debug("Deleted all user data for test user");
    }

    private static byte[] writeJpeg(BufferedImage img) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(img, "jpg", baos);
        return baos.toByteArray();
    }

    private static String configuredValue(String key, String fallback) {
        String systemValue = System.getProperty(key);
        if (systemValue != null) {
            return systemValue;
        }
        String envValue = System.getenv(key);
        if (envValue != null) {
            return envValue;
        }
        return properties.getProperty(key, fallback);
    }

    private static void sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new AssertionError("Interrupted while waiting for analysis processing", e);
        }
    }
}
