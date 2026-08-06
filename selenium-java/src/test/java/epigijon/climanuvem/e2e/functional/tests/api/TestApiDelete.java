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
 *   <li>DELETE /analysis/{id}       — remove a single analysis (HTTP 200 or 404)</li>
 *   <li>DELETE /analysis/user-data  — remove all analyses for the authenticated user (HTTP 200)</li>
 * </ul>
 */
class TestApiDelete extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /analysis/{id} returns HTTP 200 and the analysis no longer appears in history")
    void testDeleteSingleAnalysisReturns200() throws IOException {
        int analysisId = createAnalysis("Delete Me City");

        int deleteStatus = deleteStatusAuth(analysisUrl("/" + analysisId));
        Assertions.assertEquals(200, deleteStatus, "Deleting an existing analysis must return HTTP 200");

        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        Assertions.assertFalse(
                containsByField(history, "id", String.valueOf(analysisId)),
                "Deleted analysis must not appear in history");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /analysis/{id} returns HTTP 404 when the analysis does not exist")
    void testDeleteNonExistentAnalysisReturns404() throws IOException {
        int nonExistentId = Integer.MAX_VALUE;
        int status = deleteStatusAuth(analysisUrl("/" + nonExistentId));
        Assertions.assertEquals(404, status,
                "Deleting a non-existent analysis must return HTTP 404");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /analysis/user-data returns HTTP 200 and clears the user's entire history")
    void testDeleteUserDataClearsHistory() throws IOException {
        createAnalysis("Bulk Delete A");
        createAnalysis("Bulk Delete B");

        int deleteStatus = deleteStatusAuth(analysisUrl("/user-data"));
        Assertions.assertEquals(200, deleteStatus, "Deleting all user data must return HTTP 200");

        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        Assertions.assertTrue(history.isEmpty(), "History must be empty after deleting all user data");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("DELETE /analysis/user-data returns HTTP 200 even when the user has no data")
    void testDeleteUserDataWhenEmptyReturns200() throws IOException {
        deleteAllUserData();
        int status = deleteStatusAuth(analysisUrl("/user-data"));
        Assertions.assertEquals(200, status,
                "DELETE /user-data must return 200 even when there is nothing to delete");
    }
}
