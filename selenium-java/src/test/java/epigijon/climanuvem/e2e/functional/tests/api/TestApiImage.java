package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates authenticated image delivery:
 * <ul>
 *   <li>GET /api/v1/analyses/{id}/image — JPEG bytes for the owner, 401 without credentials, 404 for unknown id</li>
 *   <li>GET /uploads/... — the public static mount no longer exists (404)</li>
 *   <li>{@code imageUrl} is the relative path of the image endpoint</li>
 * </ul>
 */
class TestApiImage extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /api/v1/analyses/{id}/image returns the JPEG for the owner")
    void testOwnerGetsJpeg() throws IOException {
        int id = createAnalysis("Image City " + unique());
        ApiResponse response = getBytesResponse(analysisImageUrl(id), true);
        byte[] bytes = response.getBodyBytes();
        String contentType = response.getHeader("Content-Type");

        Assertions.assertAll(
                () -> Assertions.assertEquals(200, response.getStatusCode(), "HTTP status"),
                () -> Assertions.assertTrue(contentType != null && contentType.startsWith("image/jpeg"),
                        "Content-Type must be image/jpeg but was " + contentType),
                () -> Assertions.assertTrue(bytes.length > 3, "Body must not be empty"),
                () -> Assertions.assertTrue(bytes[0] == (byte) 0xFF && bytes[1] == (byte) 0xD8
                        && bytes[2] == (byte) 0xFF, "Body must start with the JPEG magic FF D8 FF"));
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /api/v1/analyses/{id}/image without Authorization returns 401 NOT_AUTHENTICATED")
    void testImageRequiresAuth() throws IOException {
        int id = createAnalysis("Image Auth City");
        assertProblem(getBytesResponse(analysisImageUrl(id), false), 401, "NOT_AUTHENTICATED");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/analyses/{id}/image for an unknown id returns 404 ANALYSIS_NOT_FOUND")
    void testImageUnknownId() throws IOException {
        assertProblem(getBytesResponse(analysisImageUrl(999999999), true), 404, "ANALYSIS_NOT_FOUND");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /uploads/anything.jpg returns 404 (no public static mount)")
    void testUploadsMountIsGone() throws IOException {
        Assertions.assertEquals(404, getStatus(rootUrl("/uploads/anything.jpg")),
                "/uploads must no longer be served publicly");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("imageUrl of an analysis is the relative /api/v1/analyses/{id}/image path")
    void testImageUrlIsRelativeImageEndpoint() throws IOException {
        int id = createAnalysis("ImageUrl City");
        JsonObject analysis = getJsonObjectAuth(analysisUrl(id));
        Assertions.assertEquals("/api/v1/analyses/" + id + "/image", analysis.get("imageUrl").getAsString());
    }
}
