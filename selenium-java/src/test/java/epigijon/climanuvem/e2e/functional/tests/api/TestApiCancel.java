package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates the cancellation endpoint:
 * <ul>
 *   <li>PATCH /api/v1/analyses/{id} with {@code {"status": "cancelled"}} — cancel an in-progress analysis</li>
 * </ul>
 * Tests run with DISABLE_WORKER=true so uploaded analyses stay in 'analyzing'
 * status, making cancellation deterministic without Ollama.
 */
class TestApiCancel extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /api/v1/analyses/{id} returns HTTP 200 and the updated analysis with status 'cancelled'")
    void testCancelAnalysisReturns200() throws IOException {
        int analysisId = createAnalysis("Cancel Me City");

        ApiResponse response = cancelAnalysis(analysisId);
        Assertions.assertEquals(200, response.getStatusCode(),
                "Cancelling an 'analyzing' task must return HTTP 200");
        JsonObject body = response.json();
        Assertions.assertAll(
                () -> Assertions.assertEquals(analysisId, body.get("id").getAsInt(), "Updated object 'id'"),
                () -> Assertions.assertEquals("cancelled", body.get("status").getAsString(),
                        "Updated object must have status 'cancelled'")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /api/v1/analyses/{id} returns 409 ANALYSIS_NOT_CANCELLABLE when already cancelled")
    void testCancelAlreadyCancelledReturns409() throws IOException {
        int analysisId = createAnalysis("Double Cancel City");

        cancelAnalysis(analysisId);

        assertProblem(cancelAnalysis(analysisId), 409, "ANALYSIS_NOT_CANCELLABLE");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /api/v1/analyses/{id} returns 404 ANALYSIS_NOT_FOUND for a non-existent analysis")
    void testCancelNonExistentAnalysisReturns404() throws IOException {
        assertProblem(cancelAnalysis(Integer.MAX_VALUE), 404, "ANALYSIS_NOT_FOUND");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /api/v1/analyses/{id} with a status other than 'cancelled' returns HTTP 422")
    void testPatchWithInvalidStatusReturns422() throws IOException {
        int analysisId = createAnalysis("Bad Status City");

        ApiResponse response = patchStatusResponse(analysisUrl(analysisId), "completed", true);
        Assertions.assertEquals(422, response.getStatusCode(),
                "Only the 'cancelled' status can be requested");

        JsonObject stored = getJsonObjectAuth(analysisUrl(analysisId));
        Assertions.assertEquals("analyzing", stored.get("status").getAsString(),
                "A rejected PATCH must not change the analysis");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /api/v1/analyses/{id} without Authorization header returns HTTP 401")
    void testCancelRequiresAuth() throws IOException {
        int analysisId = createAnalysis("Auth Check City");
        ApiResponse response = patchStatusResponse(analysisUrl(analysisId), "cancelled", false);
        assertProblem(response, 401, "NOT_AUTHENTICATED");
    }
}
