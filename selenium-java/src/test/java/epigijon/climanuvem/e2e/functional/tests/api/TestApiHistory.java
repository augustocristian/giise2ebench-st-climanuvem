package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
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
 *   <li>GET /api/v1/analyses — returns all analyses for the authenticated user</li>
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
    @DisplayName("GET /api/v1/analyses returns HTTP 200 with an empty list when the user has no analyses")
    void testHistoryInitiallyEmpty() throws IOException {
        deleteAllUserData();

        Assertions.assertEquals(200, getStatusAuth(analysesUrl("")),
                "History endpoint must return HTTP 200");

        JsonArray history = getJsonArrayAuth(analysesUrl(""));
        Assertions.assertTrue(history.isEmpty(), "History must be empty for a fresh test user");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /api/v1/analyses returns HTTP 200 and lists the uploaded analysis")
    void testHistoryAfterUploadContainsEntry() throws IOException {
        int analysisId = createAnalysis("Oviedo, Spain");

        JsonArray history = getJsonArrayAuth(analysesUrl(""));
        Assertions.assertFalse(history.isEmpty(), "History must contain the uploaded analysis");
        Assertions.assertTrue(
                containsByField(history, "id", String.valueOf(analysisId)),
                "History must include the analysis with id=" + analysisId);
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /api/v1/analyses returns entries with id, status, date, location, imageUrl, and results")
    void testHistoryEntryHasRequiredFields() throws IOException {
        createAnalysis("Test City");

        JsonArray history = getJsonArrayAuth(analysesUrl(""));
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
    @DisplayName("GET /api/v1/analyses results block contains cloudTypes, cloudDetails, forecast, and warnings")
    void testHistoryResultsBlockHasRequiredFields() throws IOException {
        createAnalysis("Results Field City");

        JsonArray history = getJsonArrayAuth(analysesUrl(""));
        Assertions.assertFalse(history.isEmpty(), "History must not be empty");

        JsonObject results = history.get(0).getAsJsonObject().getAsJsonObject("results");
        Assertions.assertAll(
                () -> Assertions.assertTrue(results.has("cloudTypes"),   "results must have 'cloudTypes'"),
                () -> Assertions.assertTrue(results.has("cloudDetails"), "results must have 'cloudDetails'"),
                () -> Assertions.assertTrue(results.has("forecast"),     "results must have 'forecast'"),
                () -> Assertions.assertTrue(results.has("warnings"),     "results must have 'warnings'")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /api/v1/analyses/{id} returns HTTP 200 with the analysis object")
    void testGetSingleAnalysisReturns200() throws IOException {
        int analysisId = createAnalysis("Single Get City");

        ApiResponse response = getResponseAuth(analysisUrl(analysisId));
        JsonObject analysis = response.json();
        Assertions.assertAll(
                () -> Assertions.assertEquals(200, response.getStatusCode(), "Existing analysis must return 200"),
                () -> Assertions.assertEquals(analysisId, analysis.get("id").getAsInt(), "'id'"),
                () -> Assertions.assertEquals("analyzing", analysis.get("status").getAsString(), "'status'"),
                () -> Assertions.assertEquals("Single Get City", analysis.get("location").getAsString(),
                        "'location'"),
                () -> Assertions.assertTrue(analysis.has("imageUrl"), "Must have 'imageUrl'"),
                () -> Assertions.assertTrue(analysis.has("results"), "Must have 'results'"),
                () -> Assertions.assertTrue(analysis.get("date").getAsString().endsWith("Z"),
                        "'date' must be an ISO-8601 UTC timestamp ending in 'Z'")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/analyses/{id} returns 404 ANALYSIS_NOT_FOUND for a non-existent analysis")
    void testGetSingleNonExistentReturns404() throws IOException {
        assertProblem(getResponseAuth(analysisUrl(Integer.MAX_VALUE)), 404, "ANALYSIS_NOT_FOUND");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("GET /api/v1/analyses supports page/size pagination and the X-Total-Count header")
    void testHistoryPaginationAndTotalCount() throws IOException {
        deleteAllUserData();
        int first = createAnalysis("Page City 1");
        int second = createAnalysis("Page City 2");
        int third = createAnalysis("Page City 3");

        ApiResponse page0 = getResponseAuth(analysesUrl("?page=0&size=2"));
        ApiResponse page1 = getResponseAuth(analysesUrl("?page=1&size=2"));
        JsonArray items0 = JsonParser.parseString(page0.getBody()).getAsJsonArray();
        JsonArray items1 = JsonParser.parseString(page1.getBody()).getAsJsonArray();

        Assertions.assertAll(
                () -> Assertions.assertEquals("3", page0.getHeader("X-Total-Count"), "X-Total-Count"),
                () -> Assertions.assertEquals(2, items0.size(), "First page holds 'size' items"),
                () -> Assertions.assertEquals(1, items1.size(), "Second page holds the remainder"),
                () -> Assertions.assertEquals(third, items0.get(0).getAsJsonObject().get("id").getAsInt(),
                        "Newest first"),
                () -> Assertions.assertEquals(second, items0.get(1).getAsJsonObject().get("id").getAsInt(),
                        "Newest first"),
                () -> Assertions.assertEquals(first, items1.get(0).getAsJsonObject().get("id").getAsInt(),
                        "Oldest last")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/analyses rejects out-of-range pagination parameters with HTTP 422")
    void testHistoryInvalidPaginationReturns422() throws IOException {
        Assertions.assertAll(
                () -> Assertions.assertEquals(422, getStatusAuth(analysesUrl("?size=0")), "size=0"),
                () -> Assertions.assertEquals(422, getStatusAuth(analysesUrl("?size=101")), "size=101"),
                () -> Assertions.assertEquals(422, getStatusAuth(analysesUrl("?page=-1")), "page=-1")
        );
    }
}
