// API spec for the public health-check endpoints that require no
// authentication, mirroring selenium-java's TestApiPing:
//   GET /ping  — liveness probe
//   GET /      — service status response
import { getStatus, getJson, rootUrl } from '../../support/apiClient';

describe('API: ping', () => {
  it('GET /ping returns HTTP 200 with ping:pong payload', () => {
    getStatus(rootUrl('/ping')).should('eq', 200);
    getJson(rootUrl('/ping')).then((body) => {
      expect(body).to.have.property('ping', 'pong');
    });
  });

  it('GET / returns HTTP 200 with service status payload', () => {
    getStatus(rootUrl('/')).should('eq', 200);
    getJson(rootUrl('/')).then((body) => {
      expect(body).to.have.property('service', 'ClimaNuvem API');
      expect(body).to.have.property('status', 'ok');
    });
  });
});
