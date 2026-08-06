package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonArray;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates the deletion endpoints:
 * <ul>
 *   <li>DELETE /api/v1/analyses/{id} — remove a single analysis (204 no body, or 404)</li>
 *   <li>DELETE /api/v1/analyses      — remove all analyses of the authenticated user (204 no body)</li>
 * </ul>
 */
class TestApiDelete extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /api/v1/analyses/{id} returns HTTP 204 with no body and the analysis disappears")
    void testDeleteSingleAnalysisReturns204() throws IOException {
        int analysisId = createAnalysis("Delete Me City");

        ApiResponse response = deleteResponse(analysisUrl(analysisId), true);
        Assertions.assertAll(
                () -> Assertions.assertEquals(204, response.getStatusCode(),
                        "Deleting an existing analysis must return HTTP 204"),
                () -> Assertions.assertTrue(response.getBody().isEmpty(), "204 must have an empty body")
        );

        JsonArray history = getJsonArrayAuth(analysesUrl("?size=100"));
        Assertions.assertFalse(
                containsByField(history, "id", String.valueOf(analysisId)),
                "Deleted analysis must not appear in history");
        Assertions.assertEquals(404, getStatusAuth(analysisUrl(analysisId)),
                "Deleted analysis must no longer be retrievable");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /api/v1/analyses/{id} returns 404 ANALYSIS_NOT_FOUND when the analysis does not exist")
    void testDeleteNonExistentAnalysisReturns404() throws IOException {
        assertProblem(deleteResponse(analysisUrl(Integer.MAX_VALUE), true), 404, "ANALYSIS_NOT_FOUND");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /api/v1/analyses returns HTTP 204 and clears the user's entire history")
    void testDeleteCollectionClearsHistory() throws IOException {
        createAnalysis("Bulk Delete A");
        createAnalysis("Bulk Delete B");

        ApiResponse response = deleteResponse(analysesUrl(""), true);
        Assertions.assertAll(
                () -> Assertions.assertEquals(204, response.getStatusCode(),
                        "Deleting the whole collection must return HTTP 204"),
                () -> Assertions.assertTrue(response.getBody().isEmpty(), "204 must have an empty body")
        );

        JsonArray history = getJsonArrayAuth(analysesUrl(""));
        Assertions.assertTrue(history.isEmpty(), "History must be empty after deleting the collection");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /api/v1/analyses returns HTTP 204 even when the user has no data")
    void testDeleteCollectionWhenEmptyReturns204() throws IOException {
        deleteAllUserData();
        int status = deleteStatusAuth(analysesUrl(""));
        Assertions.assertEquals(204, status,
                "DELETE on the collection must return 204 even when there is nothing to delete");
    }
}
