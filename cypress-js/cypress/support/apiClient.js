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
  return `${sutUrl()}/analysis${path}`;
}

export function rootUrl(path) {
  return `${sutUrl()}${path}`;
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

export function patchStatusAuth(url) {
  return cy.request({ method: 'PATCH', url, headers: authHeaders(), failOnStatusCode: false }).its('status');
}

// ── Multipart image upload ──────────────────────────────────────────────────

/**
 * Uploads an image via POST /analysis/upload (or `url`). `imageKind` selects
 * a fixture generated in cypress/tasks/testImages.js ('test' | 'cloudy' |
 * 'noCloud' | 'empty' | 'tooLarge' | 'nonJpeg'); pass `imageBase64` instead
 * to upload arbitrary bytes. Yields `{ status, body }`.
 */
export function uploadImage({
  url = analysisUrl('/upload'),
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

export function uploadWithoutFile(location, url = analysisUrl('/upload')) {
  return cy.task('uploadWithoutFile', { url, token: testToken(), location });
}

// ── Analysis fixtures / polling ─────────────────────────────────────────────

/** Uploads a minimal test image to /analysis/upload and yields the new analysis_id. */
export function createAnalysis(location) {
  return uploadImage({ location }).its('body.analysis_id');
}

/** Deletes every analysis for the test user via DELETE /analysis/user-data. */
export function deleteAllUserData() {
  return deleteStatusAuth(analysisUrl('/user-data'));
}

export function findAnalysisInHistory(analysisId) {
  return getJsonAuth(analysisUrl('/history')).then(
    (history) => history.find((entry) => entry.id === analysisId) || null
  );
}

export function containsByField(array, field, expected) {
  return array.some((item) => String(item[field]) === String(expected));
}

/**
 * Polls GET /analysis/history until `analysisId` reaches a terminal status
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
