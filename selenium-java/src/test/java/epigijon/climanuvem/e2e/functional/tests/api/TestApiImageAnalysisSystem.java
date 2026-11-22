package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.apache.http.entity.ContentType;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Properties;

/**
 * System tests for the real image-analysis flow.
 * <p>
 * These tests require the SUT to be deployed with the analysis worker enabled
 * and Ollama available. Run them explicitly with:
 * <pre>
 *   mvn test -Dtest=TestApiImageAnalysisSystem -DREAL_OLLAMA_TESTS=true
 * </pre>
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class TestApiImageAnalysisSystem extends BaseApiClass {

    private static final long ANALYSIS_TIMEOUT_MS = configuredLong("ANALYSIS_TIMEOUT_MS", "360000");
    private static final long ANALYSIS_POLL_MS = 5000;

    @BeforeAll
    void requireRealOllamaOptIn() {
        Assumptions.assumeTrue("true".equalsIgnoreCase(System.getProperty("REAL_OLLAMA_TESTS"))
                        || "true".equalsIgnoreCase(System.getenv("REAL_OLLAMA_TESTS")),
                "Real Ollama image-analysis tests are disabled. Set REAL_OLLAMA_TESTS=true to run them.");
    }

    @BeforeEach
    void cleanUpUserData() throws IOException {
        deleteAllUserData();
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("BASE - Gallery/API JPG under 5 MB without explainability completes with cloud results")
    void baseGalleryJpgUnderLimitWithoutExplainabilityCompletesWithCloudResults() throws IOException {
        JsonObject upload = uploadAndAssertAnalyzing(createCloudyJpeg(), "base-gallery.jpg",
                ContentType.IMAGE_JPEG, "Base Gallery City", false);

        JsonObject completed = waitForCompletedAnalysis(upload.get("analysis_id").getAsInt());
        JsonArray cloudTypes = completed.getAsJsonObject("results").getAsJsonArray("cloudTypes");

        Assertions.assertFalse(cloudTypes.isEmpty(),
                "A valid cloudy JPG must complete with at least one cloud type");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("2 - Camera-origin JPG is processed like a gallery upload")
    void cameraOriginJpgIsProcessedLikeGalleryUpload() throws IOException {
        JsonObject upload = uploadAndAssertAnalyzing(createCloudyJpeg(), "camera-capture.jpg",
                ContentType.IMAGE_JPEG, "Camera City", false);

        JsonObject completed = waitForCompletedAnalysis(upload.get("analysis_id").getAsInt());

        Assertions.assertEquals("completed", completed.get("status").getAsString(),
                "A camera-origin JPG reaches the same completed state as gallery uploads at API level");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("3 - Upload with no selected file is rejected")
    void uploadWithNoSelectedFileIsRejected() throws IOException {
        int status = uploadWithoutFileStatus(analysisUrl("/upload"), "No File City");

        Assertions.assertEquals(422, status,
                "Multipart uploads without a file must be rejected as an invalid request");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("4 - Zero-byte image is rejected")
    void zeroByteImageIsRejected() throws IOException {
        int status = uploadImageStatus(analysisUrl("/upload"), createEmptyImageBytes(), "empty.jpg",
                ContentType.IMAGE_JPEG, "Empty Image City", false);

        Assertions.assertEquals(400, status,
                "Zero-byte images must be rejected with HTTP 400");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("5 - Image larger than 5 MB is rejected")
    void imageLargerThanFiveMbIsRejected() throws IOException {
        int status = uploadImageStatus(analysisUrl("/upload"), createTooLargePayload(), "too-large.jpg",
                ContentType.IMAGE_JPEG, "Too Large City", false);

        Assertions.assertEquals(413, status,
                "Images above the 5 MB limit must be rejected with HTTP 413");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("6 - Non-JPG upload is rejected")
    void nonJpgUploadIsRejected() throws IOException {
        int status = uploadImageStatus(analysisUrl("/upload"), createNonJpegPayload(), "not-a-jpg.txt",
                ContentType.TEXT_PLAIN, "Wrong Format City", false);

        Assertions.assertTrue(status >= 400,
                "Non-JPG images must be rejected by the system design");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("7 - Explainability with clouds completes with normalized bounding boxes")
    void explainabilityWithCloudsCompletesWithNormalizedBoundingBoxes() throws IOException {
        JsonObject upload = uploadAndAssertAnalyzing(createCloudyJpeg(), "explainability-clouds.jpg",
                ContentType.IMAGE_JPEG, "Explainability City", true);

        JsonObject completed = waitForCompletedAnalysis(upload.get("analysis_id").getAsInt());
        JsonArray cloudDetails = completed.getAsJsonObject("results").getAsJsonArray("cloudDetails");

        Assertions.assertTrue(hasNormalizedBox(cloudDetails),
                "Explainability enabled for a cloudy image must persist at least one normalized box");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("8 - No-cloud JPG without explainability completes without boxes")
    void noCloudJpgWithoutExplainabilityCompletesWithoutBoxes() throws IOException {
        JsonObject upload = uploadAndAssertAnalyzing(createNoCloudJpeg(), "clear-sky.jpg",
                ContentType.IMAGE_JPEG, "Clear Sky City", false);

        JsonObject completed = waitForCompletedAnalysis(upload.get("analysis_id").getAsInt());
        JsonObject results = completed.getAsJsonObject("results");

        Assertions.assertAll(
                () -> Assertions.assertTrue(isNoCloudCompatible(results),
                        "A clear-sky image should produce no clouds or the no_cloud label"),
                () -> Assertions.assertFalse(hasNormalizedBox(results.getAsJsonArray("cloudDetails")),
                        "Explainability disabled must not require bounding boxes")
        );
    }

    private JsonObject uploadAndAssertAnalyzing(byte[] imageBytes, String filename, ContentType contentType,
            String location, boolean includeExplainability) throws IOException {
        ApiResponse response = uploadImageResponse(analysisUrl("/upload"), imageBytes, filename, contentType,
                location, includeExplainability);

        Assertions.assertEquals(200, response.getStatusCode(), "Upload must return HTTP 200");
        JsonObject body = JsonParser.parseString(response.getBody()).getAsJsonObject();
        Assertions.assertAll(
                () -> Assertions.assertTrue(body.has("analysis_id"), "Upload response must contain analysis_id"),
                () -> Assertions.assertEquals("analyzing", body.get("status").getAsString(),
                        "Upload response must start in analyzing status"),
                () -> Assertions.assertTrue(body.get("analysis_id").getAsInt() > 0,
                        "analysis_id must be positive")
        );
        return body;
    }

    private JsonObject waitForCompletedAnalysis(int analysisId) throws IOException {
        JsonObject analysis = waitForAnalysisTerminalStatus(analysisId, ANALYSIS_TIMEOUT_MS, ANALYSIS_POLL_MS);

        Assertions.assertNotNull(analysis,
                "Analysis " + analysisId + " must appear in history before timeout");
        String status = analysis.get("status").getAsString();
        Assertions.assertNotEquals("cancelled", status,
                "Analysis " + analysisId + " unexpectedly cancelled - check the Ollama worker logs");
        Assertions.assertEquals("completed", status,
                "Analysis " + analysisId + " must complete successfully");
        return analysis;
    }

    private boolean hasNormalizedBox(JsonArray cloudDetails) {
        if (cloudDetails == null) {
            return false;
        }

        for (JsonElement detailElement : cloudDetails) {
            if (!detailElement.isJsonObject()) {
                continue;
            }
            JsonObject detail = detailElement.getAsJsonObject();
            if (!detail.has("box") || detail.get("box").isJsonNull()) {
                continue;
            }
            JsonArray box = detail.getAsJsonArray("box");
            if (box.size() != 4) {
                continue;
            }
            boolean normalized = true;
            for (JsonElement coordinate : box) {
                double value = coordinate.getAsDouble();
                normalized = normalized && value >= 0.0 && value <= 1.0;
            }
            if (normalized) {
                return true;
            }
        }
        return false;
    }

    private boolean isNoCloudCompatible(JsonObject results) {
        JsonArray cloudTypes = results.getAsJsonArray("cloudTypes");
        if (cloudTypes == null || cloudTypes.isEmpty()) {
            return true;
        }

        for (JsonElement cloudType : cloudTypes) {
            if ("no_cloud".equals(cloudType.getAsString())) {
                return true;
            }
        }
        return false;
    }

    private static long configuredLong(String key, String fallback) {
        String systemValue = System.getProperty(key);
        if (systemValue != null) {
            return Long.parseLong(systemValue);
        }
        String envValue = System.getenv(key);
        if (envValue != null) {
            return Long.parseLong(envValue);
        }

        Properties properties = new Properties();
        try {
            properties.load(Files.newInputStream(Paths.get("src/test/resources/test.properties")));
            return Long.parseLong(properties.getProperty(key, fallback));
        } catch (IOException e) {
            return Long.parseLong(fallback);
        }
    }
}
