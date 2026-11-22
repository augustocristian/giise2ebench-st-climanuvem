package epigijon.climanuvem.e2e.functional.common;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.client.methods.HttpDelete;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPatch;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpRequestBase;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.entity.mime.content.ByteArrayBody;
import org.apache.http.entity.mime.content.StringBody;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
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
        private final Map<String, String> headers;
        private final byte[] bodyBytes;

        ApiResponse(int statusCode, String body, Map<String, String> headers, byte[] bodyBytes) {
            this.statusCode = statusCode;
            this.body = body;
            this.headers = headers;
            this.bodyBytes = bodyBytes;
        }

        /** Raw response body bytes (use for binary payloads such as images). */
        public byte[] getBodyBytes() {
            return bodyBytes;
        }

        /** Case-insensitive header lookup; null when absent. */
        public String getHeader(String name) {
            return headers.get(name.toLowerCase(Locale.ROOT));
        }

        public JsonObject json() {
            return JsonParser.parseString(body).getAsJsonObject();
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

    /** Builds {@code <sut>/api/v1/analyses<path>}; {@code path} is empty or starts with "/" or "?". */
    protected String analysesUrl(String path) {
        return sutUrl + "/api/v1/analyses" + path;
    }

    protected String analysisUrl(int id) {
        return analysesUrl("/" + id);
    }

    /** Builds {@code <sut>/api/v1<path>}; {@code path} is empty or starts with "/". */
    protected String apiUrl(String path) {
        return sutUrl + "/api/v1" + path;
    }

    /** Builds {@code <sut><path>} with no version prefix (used to assert removed legacy routes). */
    protected String rootUrl(String path) {
        return sutUrl + path;
    }

    /** URL of {@code GET /api/v1/analyses/{id}/image}. */
    protected String analysisImageUrl(int id) {
        return analysisUrl(id) + "/image";
    }

    // ── Generic HTTP ─────────────────────────────────────────────────────────

    /** Request with an arbitrary HTTP method (used e.g. to verify 405 responses). */
    private static class MethodRequest extends HttpRequestBase {
        private final String method;

        MethodRequest(String method, String url) {
            this.method = method;
            setURI(URI.create(url));
        }

        @Override
        public String getMethod() {
            return method;
        }
    }

    /** Executes a request and captures status, headers and body. */
    protected ApiResponse execute(HttpUriRequest request) throws IOException {
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity entity = response.getEntity();
            byte[] bytes = entity != null ? EntityUtils.toByteArray(entity) : new byte[0];
            java.nio.charset.Charset charset = java.nio.charset.StandardCharsets.ISO_8859_1;
            if (entity != null) {
                ContentType ct = ContentType.get(entity);
                if (ct != null && ct.getCharset() != null) {
                    charset = ct.getCharset();
                }
            }
            String body = new String(bytes, charset);
            Map<String, String> headers = new HashMap<>();
            for (Header header : response.getAllHeaders()) {
                headers.put(header.getName().toLowerCase(Locale.ROOT), header.getValue());
            }
            int status = response.getStatusLine().getStatusCode();
            log.debug("{} {} -> {} ({} chars)", request.getMethod(), request.getURI(), status, body.length());
            return new ApiResponse(status, body, headers, bytes);
        }
    }

    private static <T extends HttpUriRequest> T withAuth(T request, boolean auth) {
        request.addHeader("Accept", "application/json");
        if (auth) {
            request.addHeader("Authorization", "Bearer " + testToken);
        }
        return request;
    }

    /** Sends a body-less request with an arbitrary method. */
    protected ApiResponse requestResponse(String method, String url, boolean auth) throws IOException {
        return execute(withAuth(new MethodRequest(method, url), auth));
    }

    // ── Unauthenticated HTTP ─────────────────────────────────────────────────

    protected String get(String url) throws IOException {
        return getResponse(url).getBody();
    }

    protected int getStatus(String url) throws IOException {
        return getResponse(url).getStatusCode();
    }

    protected ApiResponse getResponse(String url) throws IOException {
        return execute(withAuth(new HttpGet(url), false));
    }

    // ── Authenticated HTTP ───────────────────────────────────────────────────

    protected String getAuth(String url) throws IOException {
        return getResponseAuth(url).getBody();
    }

    protected ApiResponse getResponseAuth(String url) throws IOException {
        return execute(withAuth(new HttpGet(url), true));
    }

    /** GET accepting any content type; read binary payloads with {@link ApiResponse#getBodyBytes()}. */
    protected ApiResponse getBytesResponse(String url, boolean auth) throws IOException {
        HttpGet request = new HttpGet(url);
        request.addHeader("Accept", "*/*");
        if (auth) {
            request.addHeader("Authorization", "Bearer " + testToken);
        }
        return execute(request);
    }

    protected int getStatusAuth(String url) throws IOException {
        return getResponseAuth(url).getStatusCode();
    }

    protected ApiResponse deleteResponse(String url, boolean auth) throws IOException {
        return execute(withAuth(new HttpDelete(url), auth));
    }

    protected int deleteStatusAuth(String url) throws IOException {
        return deleteResponse(url, true).getStatusCode();
    }

    /** {@code PATCH url} with JSON body {@code {"status": <status>}}. */
    protected ApiResponse patchStatusResponse(String url, String status, boolean auth) throws IOException {
        return patchJsonResponse(url, "{\"status\": \"" + status + "\"}", auth);
    }

    protected ApiResponse patchJsonResponse(String url, String json, boolean auth) throws IOException {
        HttpPatch request = withAuth(new HttpPatch(url), auth);
        request.setEntity(new StringEntity(json, ContentType.APPLICATION_JSON));
        return execute(request);
    }

    /** Cancels an analysis via {@code PATCH /api/v1/analyses/{id}} with {@code {"status":"cancelled"}}. */
    protected ApiResponse cancelAnalysis(int id) throws IOException {
        return patchStatusResponse(analysisUrl(id), "cancelled", true);
    }

    // ── Multipart image upload ────────────────────────────────────────────────

    protected String uploadImage(String url, byte[] imageBytes, String location) throws IOException {
        return uploadImageResponse(url, imageBytes, "test.jpg", ContentType.IMAGE_JPEG, location, null, true)
                .getBody();
    }

    protected int uploadImageStatus(String url, byte[] imageBytes, String location) throws IOException {
        return uploadImageResponse(url, imageBytes, "test.jpg", ContentType.IMAGE_JPEG, location, null, true)
                .getStatusCode();
    }

    /** Uploads a valid test JPEG to {@code POST /api/v1/analyses} and returns the full response. */
    protected ApiResponse uploadTestImage(String location) throws IOException {
        return uploadImageResponse(analysesUrl(""), createTestImage(), "test.jpg", ContentType.IMAGE_JPEG,
                location, null, true);
    }

    protected String uploadImage(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        return uploadImageResponse(url, imageBytes, filename, contentType, location, includeExplainability)
                .getBody();
    }

    protected ApiResponse uploadImageResponse(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        return uploadImageResponse(url, imageBytes, filename, contentType, location, includeExplainability, true);
    }

    /** Multipart upload with camelCase form fields; {@code includeExplainability} omitted when null. */
    protected ApiResponse uploadImageResponse(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, Boolean includeExplainability, boolean auth) throws IOException {
        HttpPost request = withAuth(new HttpPost(url), auth);
        MultipartEntityBuilder builder = MultipartEntityBuilder.create()
                .addPart("file", new ByteArrayBody(imageBytes, contentType, filename))
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN));
        if (includeExplainability != null) {
            builder.addPart("includeExplainability",
                    new StringBody(String.valueOf(includeExplainability), ContentType.TEXT_PLAIN));
        }
        request.setEntity(builder.build());
        return execute(request);
    }

    protected int uploadImageStatus(String url, byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        return uploadImageResponse(url, imageBytes, filename, contentType, location, includeExplainability)
                .getStatusCode();
    }

    protected ApiResponse uploadWithoutFileResponse(String url, String location) throws IOException {
        HttpPost request = withAuth(new HttpPost(url), true);
        request.setEntity(MultipartEntityBuilder.create()
                .addPart("location", new StringBody(location, ContentType.TEXT_PLAIN))
                .build());
        return execute(request);
    }

    protected int uploadWithoutFileStatus(String url, String location) throws IOException {
        return uploadWithoutFileResponse(url, location).getStatusCode();
    }

    /** Asserts the uniform problem+json error body: HTTP status and machine-code detail. */
    protected static void assertProblem(ApiResponse response, int expectedStatus, String expectedDetail) {
        String contentType = response.getHeader("Content-Type");
        JsonObject body = JsonParser.parseString(response.getBody()).getAsJsonObject();
        Assertions.assertAll(
                () -> Assertions.assertEquals(expectedStatus, response.getStatusCode(), "HTTP status"),
                () -> Assertions.assertTrue(
                        contentType != null && contentType.startsWith("application/problem+json"),
                        "Content-Type must be application/problem+json but was " + contentType),
                () -> Assertions.assertEquals(expectedStatus, body.get("status").getAsInt(), "problem 'status'"),
                () -> Assertions.assertEquals(expectedDetail, body.get("detail").getAsString(),
                        "problem 'detail' machine code"));
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
        JsonArray history = getJsonArrayAuth(analysesUrl("?size=100"));
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
     * Uploads a test image to {@code POST /api/v1/analyses} and returns the
     * assigned analysis ID.
     */
    protected int createAnalysis(String location) throws IOException {
        byte[] img = createTestImage();
        String response = uploadImage(analysesUrl(""), img, location);
        return JsonParser.parseString(response).getAsJsonObject().get("id").getAsInt();
    }

    /**
     * Deletes all analysis records for the test user via
     * {@code DELETE /api/v1/analyses}.
     * Call this in {@code @BeforeAll} for tests that require an empty history.
     */
    protected void deleteAllUserData() throws IOException {
        deleteStatusAuth(analysesUrl(""));
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
