// API spec for the deletion endpoints, mirroring selenium-java's
// TestApiDelete:
//   DELETE /api/v1/analyses/{id} — remove a single analysis (204 or 404)
//   DELETE /api/v1/analyses      — remove all analyses for the user (204)
import { createAnalysis, deleteAuth, deleteAllUserData, getJsonAuth, getAuth, expectProblem, analysisUrl, containsByField } from '../../support/apiClient';

const NON_EXISTENT_ID = 2147483647; // Integer.MAX_VALUE, mirroring the Java fixture

describe('API: delete', () => {
  it('DELETE /api/v1/analyses/{id} returns HTTP 204 with no body and the analysis disappears', () => {
    createAnalysis('Delete Me City').then((analysisId) => {
      deleteAuth(analysisUrl(`/${analysisId}`)).then((response) => {
        expect(response.status).to.eq(204);
        expect(response.body).to.be.oneOf(['', null, undefined]);
      });
      getAuth(analysisUrl(`/${analysisId}`)).its('status').should('eq', 404);
      getJsonAuth(analysisUrl('')).then((history) => {
        expect(containsByField(history, 'id', analysisId)).to.eq(false);
      });
    });
  });

  it('DELETE /api/v1/analyses/{id} returns HTTP 404 ANALYSIS_NOT_FOUND when the analysis does not exist', () => {
    deleteAuth(analysisUrl(`/${NON_EXISTENT_ID}`)).then((response) =>
      expectProblem(response, 404, 'ANALYSIS_NOT_FOUND')
    );
  });

  it("DELETE /api/v1/analyses returns HTTP 204 with no body and clears the user's entire history", () => {
    createAnalysis('Bulk Delete A');
    createAnalysis('Bulk Delete B');
    deleteAuth(analysisUrl('')).then((response) => {
      expect(response.status).to.eq(204);
      expect(response.body).to.be.oneOf(['', null, undefined]);
    });
    getJsonAuth(analysisUrl('')).should('have.length', 0);
  });

  it('DELETE /api/v1/analyses returns HTTP 204 even when the user has no data', () => {
    deleteAllUserData();
    deleteAllUserData().should('eq', 204);
  });
});
