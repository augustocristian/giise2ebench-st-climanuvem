// API spec for the cancellation endpoint, mirroring selenium-java's
// TestApiCancel:
//   PATCH /analysis/{id}/cancel — cancel an in-progress analysis
// Runs with DISABLE_WORKER=true so uploaded analyses stay in 'analyzing'
// status, making cancellation deterministic without Ollama.
import { createAnalysis, patchStatusAuth, getStatus, analysisUrl } from '../../support/apiClient';

const NON_EXISTENT_ID = 2147483647; // Integer.MAX_VALUE, mirroring the Java fixture

describe('API: cancel', () => {
  it("returns HTTP 200 for an analysis in 'analyzing' status", () => {
    createAnalysis('Cancel Me City').then((analysisId) => {
      patchStatusAuth(analysisUrl(`/${analysisId}/cancel`)).should('eq', 200);
    });
  });

  it('returns HTTP 400 when the analysis is already cancelled', () => {
    createAnalysis('Double Cancel City').then((analysisId) => {
      patchStatusAuth(analysisUrl(`/${analysisId}/cancel`));
      patchStatusAuth(analysisUrl(`/${analysisId}/cancel`)).should('eq', 400);
    });
  });

  it('returns HTTP 404 for a non-existent analysis', () => {
    patchStatusAuth(analysisUrl(`/${NON_EXISTENT_ID}/cancel`)).should('eq', 404);
  });

  it('returns HTTP 403 without Authorization header', () => {
    createAnalysis('Auth Check City').then((analysisId) => {
      getStatus(analysisUrl(`/${analysisId}/cancel`)).should('eq', 403);
    });
  });
});
