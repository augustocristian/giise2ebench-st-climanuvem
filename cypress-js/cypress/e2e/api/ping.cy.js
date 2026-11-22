// API spec for the public health-check endpoints that require no
// authentication, mirroring selenium-java's TestApiPing:
//   GET /api/v1/ping — liveness probe
//   GET /api/v1/     — service status response (/api/v1 works too)
// The unversioned /ping no longer exists.
import { getStatus, getJson, rootUrl, legacyUrl } from '../../support/apiClient';

describe('API: ping', () => {
  it('GET /api/v1/ping returns HTTP 200 with ping:pong payload', () => {
    getStatus(rootUrl('/ping')).should('eq', 200);
    getJson(rootUrl('/ping')).then((body) => {
      expect(body).to.have.property('ping', 'pong');
    });
  });

  it('GET /api/v1/ returns HTTP 200 with service status payload', () => {
    getStatus(rootUrl('/')).should('eq', 200);
    getJson(rootUrl('/')).then((body) => {
      expect(body).to.have.property('service', 'ClimaNuvem API');
      expect(body).to.have.property('status', 'ok');
    });
  });

  it('GET /api/v1 (no trailing slash) returns HTTP 200', () => {
    getStatus(rootUrl('')).should('eq', 200);
  });

  it('legacy GET /ping returns HTTP 404', () => {
    getStatus(legacyUrl('/ping')).should('eq', 404);
  });
});
