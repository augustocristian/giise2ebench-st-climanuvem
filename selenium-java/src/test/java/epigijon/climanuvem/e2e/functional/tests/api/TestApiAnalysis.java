package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates the image-upload endpoint:
 * <ul>
 *   <li>POST /analysis/upload — creates an analysis record and returns its ID</li>
 * </ul>
 * Tests run with DISABLE_WORKER=true, so uploaded analyses remain in 'analyzing'
 * status — no Ollama connection is required.
 */
class TestApiAnalysis extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /analysis/upload returns HTTP 200 with status 'analyzing' and a positive analysis_id")
    void testUploadImageReturnsAnalyzingStatus() throws IOException {
        byte[] img = createTestImage();
        String response = uploadImage(analysisUrl("/upload"), img, "Test Location");
        JsonObject body = JsonParser.parseString(response).getAsJsonObject();

        Assertions.assertAll(
                () -> Assertions.assertTrue(body.has("analysis_id"),
                        "Response must contain 'analysis_id'"),
                () -> Assertions.assertTrue(body.has("status"),
                        "Response must contain 'status'"),
                () -> Assertions.assertEquals("analyzing", body.get("status").getAsString(),
                        "'status' must be 'analyzing' immediately after upload"),
                () -> Assertions.assertTrue(body.get("analysis_id").getAsInt() > 0,
                        "'analysis_id' must be a positive integer")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /analysis/upload returns HTTP 200")
    void testUploadImageHttpStatus() throws IOException {
        byte[] img = createTestImage();
        int status = uploadImageStatus(analysisUrl("/upload"), img, "Another Location");
        Assertions.assertEquals(200, status, "Upload must return HTTP 200");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /analysis/upload with a custom location stores the location in the response")
    void testUploadWithCustomLocation() throws IOException {
        String location = "Madrid, Spain " + unique();
        byte[] img = createTestImage();
        String response = uploadImage(analysisUrl("/upload"), img, location);
        JsonObject body = JsonParser.parseString(response).getAsJsonObject();
        Assertions.assertTrue(body.has("analysis_id"),
                "Upload with custom location must return 'analysis_id'");
        Assertions.assertTrue(body.get("analysis_id").getAsInt() > 0,
                "'analysis_id' must be positive");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("Two consecutive uploads produce distinct analysis IDs")
    void testConsecutiveUploadsHaveDistinctIds() throws IOException {
        int id1 = createAnalysis("Location A");
        int id2 = createAnalysis("Location B");
        Assertions.assertNotEquals(id1, id2, "Each upload must produce a unique analysis_id");
    }
}
