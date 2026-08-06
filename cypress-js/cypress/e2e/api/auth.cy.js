// API spec for authentication enforcement, mirroring selenium-java's
// TestApiAuth:
//   GET    /api/v1/test             — requires a Bearer token (test mode only)
//   GET/POST/DELETE /api/v1/analyses and GET/PATCH/DELETE /api/v1/analyses/{id}
// Missing Authorization header -> HTTP 401 NOT_AUTHENTICATED with
// WWW-Authenticate: Bearer. There is deliberately no invalid-token spec: the
// suite runs against TEST_MODE=true, where the backend accepts any Bearer token.
import { getStatusAuth, getJsonAuth, requestNoAuth, expectProblem, analysisUrl, rootUrl } from '../../support/apiClient';

describe('API: auth', () => {
  it('GET /api/v1/test without Authorization header returns HTTP 401', () => {
    requestNoAuth('GET', rootUrl('/test')).then((response) => {
      expectProblem(response, 401, 'NOT_AUTHENTICATED');
      expect(response.headers['www-authenticate']).to.match(/bearer/i);
    });
  });

  it('GET /api/v1/test with the test token returns HTTP 200 and user info', () => {
    getStatusAuth(rootUrl('/test')).should('eq', 200);
    getJsonAuth(rootUrl('/test')).then((body) => {
      expect(body).to.have.property('message', 'Test successful');
      expect(body).to.have.property('user');
    });
  });

  [
    ['GET', '', undefined],
    ['POST', '', undefined],
    ['DELETE', '', undefined],
    ['GET', '/1', undefined],
    ['PATCH', '/1', { status: 'cancelled' }],
    ['DELETE', '/1', undefined],
  ].forEach(([method, path, body]) => {
    it(`${method} /api/v1/analyses${path} without Authorization header returns HTTP 401`, () => {
      requestNoAuth(method, analysisUrl(path), body).then((response) => {
        expectProblem(response, 401, 'NOT_AUTHENTICATED');
      });
    });
  });
});
