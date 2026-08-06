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
 *   <li>GET /ping  — liveness probe</li>
 *   <li>GET /      — service status response</li>
 * </ul>
 */
class TestApiPing extends BaseApiClass {

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET /ping returns HTTP 200 with ping:pong payload")
    void testPingEndpoint() throws IOException {
        Assertions.assertEquals(200, getStatus(rootUrl("/ping")), "Expected HTTP 200 from /ping");

        JsonObject body = getJsonObject(rootUrl("/ping"));
        Assertions.assertTrue(body.has("ping"), "/ping response must have 'ping' field");
        Assertions.assertEquals("pong", body.get("ping").getAsString(), "'ping' field must equal 'pong'");
    }

    @AccessMode(resID = "backend", concurrency = 10, sharing = true, accessMode = "READONLY")
    @Test
    @DisplayName("GET / returns HTTP 200 with service status payload")
    void testRootEndpoint() throws IOException {
        Assertions.assertEquals(200, getStatus(rootUrl("/")), "Expected HTTP 200 from /");

        JsonObject body = getJsonObject(rootUrl("/"));
        Assertions.assertTrue(body.has("service"), "Root response must have 'service' field");
        Assertions.assertEquals("ClimaNuvem API", body.get("service").getAsString(),
                "'service' field must identify the API");
        Assertions.assertTrue(body.has("status"), "Root response must have 'status' field");
        Assertions.assertEquals("ok", body.get("status").getAsString(), "'status' field must equal 'ok'");
    }
}
