package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates the image-upload endpoint:
 * <ul>
 *   <li>POST /api/v1/analyses — creates an analysis record (202 Accepted + Location + {id, status})</li>
 *   <li>405 handling by the framework for unsupported methods</li>
 * </ul>
 * Tests run with DISABLE_WORKER=true, so uploaded analyses remain in 'analyzing'
 * status — no Ollama connection is required.
 */
class TestApiAnalysis extends BaseApiClass {

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /api/v1/analyses returns 'analyzing' status and a positive integer id")
    void testUploadImageReturnsAnalyzingStatus() throws IOException {
        ApiResponse response = uploadTestImage("Test Location");
        JsonObject body = response.json();

        Assertions.assertAll(
                () -> Assertions.assertTrue(body.has("id"), "Response must contain 'id'"),
                () -> Assertions.assertTrue(body.has("status"), "Response must contain 'status'"),
                () -> Assertions.assertFalse(body.has("analysis_id"), "Legacy 'analysis_id' must be gone"),
                () -> Assertions.assertEquals("analyzing", body.get("status").getAsString(),
                        "'status' must be 'analyzing' immediately after upload"),
                () -> Assertions.assertTrue(body.get("id").getAsInt() > 0,
                        "'id' must be a positive integer")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /api/v1/analyses returns HTTP 202 and a Location header pointing to the new analysis")
    void testUploadImageHttpStatusAndLocation() throws IOException {
        ApiResponse response = uploadTestImage("Another Location");
        int id = response.json().get("id").getAsInt();

        Assertions.assertAll(
                () -> Assertions.assertEquals(202, response.getStatusCode(), "Upload must return HTTP 202"),
                () -> Assertions.assertNotNull(response.getHeader("Location"), "Location header is required"),
                () -> Assertions.assertTrue(response.getHeader("Location").endsWith("/api/v1/analyses/" + id),
                        "Location must end with /api/v1/analyses/" + id + " but was "
                                + response.getHeader("Location"))
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /api/v1/analyses with a custom location stores it on the created analysis")
    void testUploadWithCustomLocation() throws IOException {
        String location = "Madrid, Spain " + unique();
        int id = createAnalysis(location);

        JsonObject analysis = getJsonObjectAuth(analysisUrl(id));
        Assertions.assertEquals(location, analysis.get("location").getAsString(),
                "The location sent in the upload must be stored");
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("Two consecutive uploads produce distinct analysis IDs")
    void testConsecutiveUploadsHaveDistinctIds() throws IOException {
        int id1 = createAnalysis("Location A");
        int id2 = createAnalysis("Location B");
        Assertions.assertNotEquals(id1, id2, "Each upload must produce a unique id");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("PUT /api/v1/analyses returns HTTP 405 with an Allow header")
    void testUnsupportedMethodOnCollectionReturns405() throws IOException {
        ApiResponse response = requestResponse("PUT", analysesUrl(""), true);
        String allow = response.getHeader("Allow");

        Assertions.assertAll(
                () -> Assertions.assertEquals(405, response.getStatusCode(), "PUT on the collection is not allowed"),
                () -> assertAllowContains(allow, "GET", "POST", "DELETE")
        );
    }

    @AccessMode(resID = "analysis", concurrency = 1, sharing = false, accessMode = "READWRITE")
    @Test
    @DisplayName("POST /api/v1/analyses/{id} returns HTTP 405 with an Allow header")
    void testPostOnSingleAnalysisReturns405() throws IOException {
        int id = createAnalysis("Method Check City");
        ApiResponse response = requestResponse("POST", analysisUrl(id), true);
        String allow = response.getHeader("Allow");

        Assertions.assertAll(
                () -> Assertions.assertEquals(405, response.getStatusCode(),
                        "POST on a single analysis is not allowed"),
                () -> assertAllowContains(allow, "GET", "PATCH", "DELETE")
        );
    }

    private static void assertAllowContains(String allow, String... methods) {
        Assertions.assertNotNull(allow, "405 responses must carry an Allow header");
        java.util.Set<String> listed = new java.util.HashSet<>();
        for (String m : allow.split(",")) {
            listed.add(m.trim().toUpperCase(java.util.Locale.ROOT));
        }
        for (String method : methods) {
            Assertions.assertTrue(listed.contains(method), "Allow must contain " + method + " but was: " + allow);
        }
    }
}
