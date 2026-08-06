package epigijon.climanuvem.e2e.functional.tests.api;

import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates the cancellation endpoint:
 * <ul>
 *   <li>PATCH /analysis/{id}/cancel — cancel an in-progress analysis</li>
 * </ul>
 * Tests run with DISABLE_WORKER=true so uploaded analyses stay in 'analyzing'
 * status, making cancellation deterministic without Ollama.
 */
class TestApiCancel extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /analysis/{id}/cancel returns HTTP 200 for an analysis in 'analyzing' status")
    void testCancelAnalysisReturns200() throws IOException {
        int analysisId = createAnalysis("Cancel Me City");

        int cancelStatus = patchStatusAuth(analysisUrl("/" + analysisId + "/cancel"));
        Assertions.assertEquals(200, cancelStatus,
                "Cancelling an 'analyzing' task must return HTTP 200");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /analysis/{id}/cancel returns HTTP 400 when the analysis is already cancelled")
    void testCancelAlreadyCancelledReturns400() throws IOException {
        int analysisId = createAnalysis("Double Cancel City");

        patchStatusAuth(analysisUrl("/" + analysisId + "/cancel"));

        int secondCancelStatus = patchStatusAuth(analysisUrl("/" + analysisId + "/cancel"));
        Assertions.assertEquals(400, secondCancelStatus,
                "Cancelling an already-cancelled analysis must return HTTP 400");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /analysis/{id}/cancel returns HTTP 404 for a non-existent analysis")
    void testCancelNonExistentAnalysisReturns404() throws IOException {
        int nonExistentId = Integer.MAX_VALUE;
        int status = patchStatusAuth(analysisUrl("/" + nonExistentId + "/cancel"));
        Assertions.assertEquals(404, status,
                "Cancelling a non-existent analysis must return HTTP 404");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("PATCH /analysis/{id}/cancel without Authorization header returns HTTP 403")
    void testCancelRequiresAuth() throws IOException {
        int analysisId = createAnalysis("Auth Check City");
        int status = getStatus(analysisUrl("/" + analysisId + "/cancel"));
        Assertions.assertEquals(403, status,
                "Cancel endpoint must return 403 when no token is provided");
    }
}
