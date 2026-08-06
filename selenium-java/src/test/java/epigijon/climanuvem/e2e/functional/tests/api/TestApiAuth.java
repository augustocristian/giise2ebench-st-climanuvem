package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.apache.http.entity.ContentType;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates authentication enforcement across the API:
 * <ul>
 *   <li>GET    /api/v1/test             — requires valid Bearer token (test mode only)</li>
 *   <li>GET / POST /api/v1/analyses     — require a valid Bearer token</li>
 *   <li>GET / PATCH / DELETE /api/v1/analyses/{id} and DELETE /api/v1/analyses — require a Bearer token</li>
 * </ul>
 * Missing Authorization header → HTTP 401 NOT_AUTHENTICATED (with WWW-Authenticate: Bearer).
 * (In TEST_MODE any Bearer token is accepted, so the invalid-token path is not exercised here.)
 */
class TestApiAuth extends BaseApiClass {

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/test without Authorization header returns HTTP 401")
    void testTestEndpointRequiresAuth() throws IOException {
        Assertions.assertEquals(401, getStatus(apiUrl("/test")),
                "/api/v1/test must return 401 when no Authorization header is sent");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/test with the test token returns HTTP 200 and user info")
    void testTestEndpointWithValidToken() throws IOException {
        Assertions.assertEquals(200, getStatusAuth(apiUrl("/test")),
                "/api/v1/test must return 200 when a valid test token is provided");

        JsonObject body = getJsonObjectAuth(apiUrl("/test"));
        Assertions.assertTrue(body.has("message"), "Response must contain 'message'");
        Assertions.assertTrue(body.has("user"),    "Response must contain 'user'");
        Assertions.assertEquals("Test successful", body.get("message").getAsString(),
                "'message' must equal 'Test successful'");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/analyses without Authorization header returns 401 NOT_AUTHENTICATED")
    void testHistoryRequiresAuth() throws IOException {
        ApiResponse response = getResponse(analysesUrl(""));
        assertProblem(response, 401, "NOT_AUTHENTICATED");
        String challenge = response.getHeader("WWW-Authenticate");
        Assertions.assertTrue(challenge != null && challenge.startsWith("Bearer"),
                "401 must carry 'WWW-Authenticate: Bearer' but was " + challenge);
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("POST /api/v1/analyses without Authorization header returns 401")
    void testUploadRequiresAuth() throws IOException {
        ApiResponse response = uploadImageResponse(analysesUrl(""), createTestImage(), "test.jpg",
                ContentType.IMAGE_JPEG, "No Auth City", null, false);
        assertProblem(response, 401, "NOT_AUTHENTICATED");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/analyses/{id} without Authorization header returns 401")
    void testSingleGetRequiresAuth() throws IOException {
        assertProblem(getResponse(analysisUrl(1)), 401, "NOT_AUTHENTICATED");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("PATCH /api/v1/analyses/{id} without Authorization header returns 401")
    void testPatchRequiresAuth() throws IOException {
        assertProblem(patchStatusResponse(analysisUrl(1), "cancelled", false), 401, "NOT_AUTHENTICATED");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("DELETE /api/v1/analyses/{id} and DELETE /api/v1/analyses without Authorization header return 401")
    void testDeleteRequiresAuth() throws IOException {
        assertProblem(deleteResponse(analysisUrl(1), false), 401, "NOT_AUTHENTICATED");
        assertProblem(deleteResponse(analysesUrl(""), false), 401, "NOT_AUTHENTICATED");
    }
}
