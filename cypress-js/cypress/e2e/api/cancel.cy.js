// API spec for the cancellation endpoint, mirroring selenium-java's
// TestApiCancel:
//   PATCH /api/v1/analyses/{id}  body {"status":"cancelled"}
// Runs with DISABLE_WORKER=true so uploaded analyses stay in 'analyzing'
// status, making cancellation deterministic without Ollama.
import { createAnalysis, patchAuth, requestAuth, requestNoAuth, expectProblem, expectAllowIncludes, analysisUrl } from '../../support/apiClient';

const NON_EXISTENT_ID = 2147483647; // Integer.MAX_VALUE, mirroring the Java fixture

describe('API: cancel', () => {
  it("returns HTTP 200 and the updated analysis for an analysis in 'analyzing' status", () => {
    createAnalysis('Cancel Me City').then((analysisId) => {
      patchAuth(analysisUrl(`/${analysisId}`)).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('id', analysisId);
        expect(response.body).to.have.property('status', 'cancelled');
      });
    });
  });

  it('returns HTTP 409 ANALYSIS_NOT_CANCELLABLE when the analysis is already cancelled', () => {
    createAnalysis('Double Cancel City').then((analysisId) => {
      patchAuth(analysisUrl(`/${analysisId}`));
      patchAuth(analysisUrl(`/${analysisId}`)).then((response) =>
        expectProblem(response, 409, 'ANALYSIS_NOT_CANCELLABLE')
      );
    });
  });

  it('returns HTTP 404 ANALYSIS_NOT_FOUND for a non-existent analysis', () => {
    patchAuth(analysisUrl(`/${NON_EXISTENT_ID}`)).then((response) =>
      expectProblem(response, 404, 'ANALYSIS_NOT_FOUND')
    );
  });

  it('returns HTTP 422 when the requested status is not "cancelled"', () => {
    createAnalysis('Bad Status City').then((analysisId) => {
      patchAuth(analysisUrl(`/${analysisId}`), { status: 'completed' }).its('status').should('eq', 422);
    });
  });

  it('returns HTTP 401 without Authorization header', () => {
    createAnalysis('Auth Check City').then((analysisId) => {
      requestNoAuth('PATCH', analysisUrl(`/${analysisId}`), { status: 'cancelled' }).then((response) =>
        expectProblem(response, 401, 'NOT_AUTHENTICATED')
      );
    });
  });

  it('POST /api/v1/analyses/{id} is not allowed: HTTP 405 with Allow: GET, PATCH, DELETE', () => {
    createAnalysis('Method Check City').then((analysisId) => {
      requestAuth('POST', analysisUrl(`/${analysisId}`)).then((response) =>
        expectAllowIncludes(response, ['GET', 'PATCH', 'DELETE'])
      );
    });
  });
});
