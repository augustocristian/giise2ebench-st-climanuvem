package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates authentication enforcement across the API:
 * <ul>
 *   <li>GET  /test                 — requires valid Bearer token</li>
 *   <li>GET  /analysis/history     — requires valid Bearer token</li>
 *   <li>POST /analysis/upload      — requires valid Bearer token</li>
 * </ul>
 * Missing Authorization header → HTTP 403 (FastAPI HTTPBearer default).
 * Invalid token                 → HTTP 401 (our auth dependency).
 */
class TestApiAuth extends BaseApiClass {

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /test without Authorization header returns HTTP 403")
    void testTestEndpointRequiresAuth() throws IOException {
        Assertions.assertEquals(403, getStatus(rootUrl("/test")),
                "/test must return 403 when no Authorization header is sent");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /test with the test token returns HTTP 200 and user info")
    void testTestEndpointWithValidToken() throws IOException {
        Assertions.assertEquals(200, getStatusAuth(rootUrl("/test")),
                "/test must return 200 when a valid test token is provided");

        JsonObject body = getJsonObjectAuth(rootUrl("/test"));
        Assertions.assertTrue(body.has("message"), "Response must contain 'message'");
        Assertions.assertTrue(body.has("user"),    "Response must contain 'user'");
        Assertions.assertEquals("Test successful", body.get("message").getAsString(),
                "'message' must equal 'Test successful'");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /analysis/history without Authorization header returns HTTP 403")
    void testHistoryRequiresAuth() throws IOException {
        Assertions.assertEquals(403, getStatus(analysisUrl("/history")),
                "/analysis/history must return 403 when no token is provided");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("POST /analysis/upload without Authorization header returns HTTP 403")
    void testUploadRequiresAuth() throws IOException {
        Assertions.assertEquals(403, getStatus(analysisUrl("/upload")),
                "/analysis/upload must return 403 when no token is provided");
    }
}
