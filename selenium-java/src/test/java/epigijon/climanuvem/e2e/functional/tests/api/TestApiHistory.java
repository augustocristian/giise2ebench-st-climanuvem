package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import java.io.IOException;

/**
 * Validates the analysis history endpoint:
 * <ul>
 *   <li>GET /analysis/history — returns all analyses for the authenticated user</li>
 * </ul>
 * A {@code @BeforeAll} cleanup ensures the test user starts with an empty history,
 * making each scenario deterministic regardless of prior test runs.
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class TestApiHistory extends BaseApiClass {

    @BeforeAll
    void cleanUpUserData() throws IOException {
        deleteAllUserData();
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READONLY")
    @Test
    @DisplayName("GET /analysis/history returns HTTP 200 with an empty list when the user has no analyses")
    void testHistoryInitiallyEmpty() throws IOException {
        deleteAllUserData();

        Assertions.assertEquals(200, getStatusAuth(analysisUrl("/history")),
                "History endpoint must return HTTP 200");

        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        Assertions.assertTrue(history.isEmpty(), "History must be empty for a fresh test user");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /analysis/history returns HTTP 200 and lists the uploaded analysis")
    void testHistoryAfterUploadContainsEntry() throws IOException {
        int analysisId = createAnalysis("Oviedo, Spain");

        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        Assertions.assertFalse(history.isEmpty(), "History must contain the uploaded analysis");
        Assertions.assertTrue(
                containsByField(history, "id", String.valueOf(analysisId)),
                "History must include the analysis with id=" + analysisId);
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /analysis/history returns entries with id, status, date, location, imageUrl, and results")
    void testHistoryEntryHasRequiredFields() throws IOException {
        createAnalysis("Test City");

        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        Assertions.assertFalse(history.isEmpty(), "History must not be empty");

        JsonObject entry = history.get(0).getAsJsonObject();
        Assertions.assertAll(
                () -> Assertions.assertTrue(entry.has("id"),       "Entry must have 'id'"),
                () -> Assertions.assertTrue(entry.has("status"),   "Entry must have 'status'"),
                () -> Assertions.assertTrue(entry.has("date"),     "Entry must have 'date'"),
                () -> Assertions.assertTrue(entry.has("location"), "Entry must have 'location'"),
                () -> Assertions.assertTrue(entry.has("imageUrl"), "Entry must have 'imageUrl'"),
                () -> Assertions.assertTrue(entry.has("results"),  "Entry must have 'results'")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /analysis/history results block contains cloudTypes, cloudDetails, forecast, and warnings")
    void testHistoryResultsBlockHasRequiredFields() throws IOException {
        createAnalysis("Results Field City");

        JsonArray history = getJsonArrayAuth(analysisUrl("/history"));
        Assertions.assertFalse(history.isEmpty(), "History must not be empty");

        JsonObject results = history.get(0).getAsJsonObject().getAsJsonObject("results");
        Assertions.assertAll(
                () -> Assertions.assertTrue(results.has("cloudTypes"),   "results must have 'cloudTypes'"),
                () -> Assertions.assertTrue(results.has("cloudDetails"), "results must have 'cloudDetails'"),
                () -> Assertions.assertTrue(results.has("forecast"),     "results must have 'forecast'"),
                () -> Assertions.assertTrue(results.has("warnings"),     "results must have 'warnings'")
        );
    }
}
