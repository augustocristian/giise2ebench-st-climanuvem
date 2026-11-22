// HTTP-level test helpers, mirroring selenium-java's BaseApiClass. GET/PATCH/
// DELETE go straight through cy.request (Cypress proxies these, so the
// backend's CORS_ALLOW_ORIGINS never comes into play). Multipart upload runs
// through the Node-side `uploadImage`/`uploadWithoutFile` tasks registered in
// cypress.config.js, since cy.request only builds
// application/x-www-form-urlencoded bodies.

function sutUrl() {
  return Cypress.env('SUT_URL');
}

function testToken() {
  return Cypress.env('TEST_TOKEN');
}

function authHeaders() {
  return { Authorization: `Bearer ${testToken()}` };
}

export function analysisUrl(path) {
  return `${sutUrl()}/api/v1/analyses${path}`;
}

// Versioned non-analysis endpoints: rootUrl('/ping') -> {SUT_URL}/api/v1/ping,
// rootUrl('/') -> {SUT_URL}/api/v1/.
export function rootUrl(path) {
  return `${sutUrl()}/api/v1${path}`;
}

// Unversioned URL under the SUT root (used to assert legacy paths are gone).
export function legacyUrl(path) {
  return `${sutUrl()}${path}`;
}

/** Fetches binary content with the Bearer token; the body is a binary string (one char per byte). */
export function getBinaryAuth(url) {
  return cy.request({ url, headers: authHeaders(), encoding: 'binary', failOnStatusCode: false });
}

/** Asserts a 405 whose `Allow` header lists every expected method (case-insensitive, any order). */
export function expectAllowIncludes(response, methods) {
  expect(response.status).to.eq(405);
  expect(response.headers).to.have.property('allow');
  const allowed = String(response.headers.allow)
    .split(',')
    .map((m) => m.trim().toUpperCase());
  methods.forEach((m) => expect(allowed, `Allow: ${response.headers.allow}`).to.include(m));
}

// ── Unauthenticated HTTP ────────────────────────────────────────────────────

export function getStatus(url) {
  return cy.request({ url, failOnStatusCode: false }).its('status');
}

export function getJson(url) {
  return cy.request({ url, failOnStatusCode: false }).its('body');
}

// ── Authenticated HTTP ──────────────────────────────────────────────────────

export function getStatusAuth(url) {
  return cy.request({ url, headers: authHeaders(), failOnStatusCode: false }).its('status');
}

export function getJsonAuth(url) {
  return cy.request({ url, headers: authHeaders(), failOnStatusCode: false }).its('body');
}

export function deleteStatusAuth(url) {
  return cy.request({ method: 'DELETE', url, headers: authHeaders(), failOnStatusCode: false }).its('status');
}

export function patchStatusAuth(url, body = { status: 'cancelled' }) {
  return patchAuth(url, body).its('status');
}

// Full responses (status, headers, body) for specs that assert on more than the status.
export function requestAuth(method, url, body) {
  return cy.request({ method, url, body, headers: authHeaders(), failOnStatusCode: false });
}

export function requestNoAuth(method, url, body) {
  return cy.request({ method, url, body, failOnStatusCode: false });
}

export function getAuth(url) {
  return requestAuth('GET', url);
}

export function patchAuth(url, body = { status: 'cancelled' }) {
  return requestAuth('PATCH', url, body);
}

export function deleteAuth(url) {
  return requestAuth('DELETE', url);
}

/** Asserts a problem+json error body with the given HTTP status and machine-code detail. */
export function expectProblem(response, status, detail) {
  expect(response.status).to.eq(status);
  expect(response.headers['content-type']).to.include('application/problem+json');
  expect(response.body).to.have.property('status', status);
  if (detail !== undefined) {
    expect(response.body).to.have.property('detail', detail);
  }
}

// ── Multipart image upload ──────────────────────────────────────────────────

/**
 * Uploads an image via POST /api/v1/analyses (or `url`). `imageKind` selects
 * a fixture generated in cypress/tasks/testImages.js ('test' | 'cloudy' |
 * 'noCloud' | 'empty' | 'tooLarge' | 'nonJpeg'); pass `imageBase64` instead
 * to upload arbitrary bytes. Yields `{ status, headers, body }` (header names lower-case).
 */
export function uploadImage({
  url = analysisUrl(''),
  imageKind = 'test',
  imageBase64,
  location,
  filename,
  contentType,
  includeExplainability,
} = {}) {
  return cy.task('uploadImage', {
    url,
    token: testToken(),
    location,
    imageKind,
    imageBase64,
    filename,
    contentType,
    includeExplainability,
  });
}

export function uploadWithoutFile(location, url = analysisUrl('')) {
  return cy.task('uploadWithoutFile', { url, token: testToken(), location });
}

// ── Analysis fixtures / polling ─────────────────────────────────────────────

/** Uploads a minimal test image to POST /api/v1/analyses and yields the new analysis id. */
export function createAnalysis(location) {
  return uploadImage({ location }).its('body.id');
}

/** Deletes every analysis for the test user via DELETE /api/v1/analyses. */
export function deleteAllUserData() {
  return deleteStatusAuth(analysisUrl(''));
}

/** Fetches one analysis via GET /api/v1/analyses/{id}; yields null when it does not exist. */
export function findAnalysisInHistory(analysisId) {
  return getAuth(analysisUrl(`/${analysisId}`)).then((response) => (response.status === 200 ? response.body : null));
}

export function containsByField(array, field, expected) {
  return array.some((item) => String(item[field]) === String(expected));
}

/**
 * Polls GET /api/v1/analyses until `analysisId` reaches a terminal status
 * ('completed'/'cancelled') or `timeoutMs` elapses. Used by the real-Ollama
 * image-analysis suite; mirrors BaseApiClass#waitForAnalysisTerminalStatus.
 */
export function waitForAnalysisTerminalStatus(analysisId, { timeoutMs, pollMs = 5000 } = {}) {
  const deadline = Date.now() + (timeoutMs ?? Number(Cypress.env('ANALYSIS_TIMEOUT_MS')));

  const poll = () =>
    findAnalysisInHistory(analysisId).then((entry) => {
      const status = entry?.status;
      if (status === 'completed' || status === 'cancelled') {
        return entry;
      }
      if (Date.now() >= deadline) {
        return entry;
      }
      return cy.wait(pollMs).then(poll);
    });

  return poll();
}
