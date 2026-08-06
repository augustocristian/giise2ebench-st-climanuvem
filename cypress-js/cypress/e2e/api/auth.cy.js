// API spec for authentication enforcement, mirroring selenium-java's
// TestApiAuth:
//   GET  /test              — requires valid Bearer token
//   GET  /analysis/history  — requires valid Bearer token
//   POST /analysis/upload   — requires valid Bearer token
// Missing Authorization header -> HTTP 403 (FastAPI HTTPBearer default).
import { getStatus, getStatusAuth, getJsonAuth, analysisUrl, rootUrl } from '../../support/apiClient';

describe('API: auth', () => {
  it('GET /test without Authorization header returns HTTP 403', () => {
    getStatus(rootUrl('/test')).should('eq', 403);
  });

  it('GET /test with the test token returns HTTP 200 and user info', () => {
    getStatusAuth(rootUrl('/test')).should('eq', 200);
    getJsonAuth(rootUrl('/test')).then((body) => {
      expect(body).to.have.property('message', 'Test successful');
      expect(body).to.have.property('user');
    });
  });

  it('GET /analysis/history without Authorization header returns HTTP 403', () => {
    getStatus(analysisUrl('/history')).should('eq', 403);
  });

  it('POST /analysis/upload without Authorization header returns HTTP 403', () => {
    getStatus(analysisUrl('/upload')).should('eq', 403);
  });
});
