package epigijon.climanuvem.e2e.functional.tests.api;

import com.google.gson.JsonObject;
import epigijon.climanuvem.e2e.functional.common.BaseApiClass;
import giis.retorch.annotations.AccessMode;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;

/**
 * Validates the public health-check endpoints that require no authentication:
 * <ul>
 *   <li>GET /api/v1/ping  — liveness probe</li>
 *   <li>GET /api/v1/ and /api/v1 — service status response</li>
 *   <li>GET /ping — legacy unversioned route, removed (404)</li>
 * </ul>
 */
class TestApiPing extends BaseApiClass {

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/ping returns HTTP 200 with ping:pong payload")
    void testPingEndpoint() throws IOException {
        Assertions.assertEquals(200, getStatus(apiUrl("/ping")), "Expected HTTP 200 from /api/v1/ping");

        JsonObject body = getJsonObject(apiUrl("/ping"));
        Assertions.assertTrue(body.has("ping"), "/api/v1/ping response must have 'ping' field");
        Assertions.assertEquals("pong", body.get("ping").getAsString(), "'ping' field must equal 'pong'");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1/ returns HTTP 200 with service status payload")
    void testRootEndpoint() throws IOException {
        Assertions.assertEquals(200, getStatus(apiUrl("/")), "Expected HTTP 200 from /api/v1/");

        JsonObject body = getJsonObject(apiUrl("/"));
        Assertions.assertTrue(body.has("service"), "Root response must have 'service' field");
        Assertions.assertEquals("ClimaNuvem API", body.get("service").getAsString(),
                "'service' field must identify the API");
        Assertions.assertTrue(body.has("status"), "Root response must have 'status' field");
        Assertions.assertEquals("ok", body.get("status").getAsString(), "'status' field must equal 'ok'");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /api/v1 (no trailing slash) returns HTTP 200 with service status payload")
    void testRootEndpointWithoutTrailingSlash() throws IOException {
        Assertions.assertEquals(200, getStatus(apiUrl("")), "Expected HTTP 200 from /api/v1");
        Assertions.assertEquals("ok", getJsonObject(apiUrl("")).get("status").getAsString());
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("Legacy unversioned GET /ping returns HTTP 404")
    void testLegacyPingIsGone() throws IOException {
        Assertions.assertEquals(404, getStatus(rootUrl("/ping")), "Unversioned /ping must no longer exist");
    }
}
