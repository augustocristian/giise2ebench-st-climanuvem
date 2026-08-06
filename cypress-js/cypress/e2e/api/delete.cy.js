// API spec for the deletion endpoints, mirroring selenium-java's
// TestApiDelete:
//   DELETE /analysis/{id}       — remove a single analysis (HTTP 200 or 404)
//   DELETE /analysis/user-data  — remove all analyses for the user (HTTP 200)
import { createAnalysis, deleteStatusAuth, deleteAllUserData, getJsonAuth, analysisUrl, containsByField } from '../../support/apiClient';

const NON_EXISTENT_ID = 2147483647; // Integer.MAX_VALUE, mirroring the Java fixture

describe('API: delete', () => {
  it('DELETE /analysis/{id} returns HTTP 200 and the analysis no longer appears in history', () => {
    createAnalysis('Delete Me City').then((analysisId) => {
      deleteStatusAuth(analysisUrl(`/${analysisId}`)).should('eq', 200);
      getJsonAuth(analysisUrl('/history')).then((history) => {
        expect(containsByField(history, 'id', analysisId)).to.eq(false);
      });
    });
  });

  it('DELETE /analysis/{id} returns HTTP 404 when the analysis does not exist', () => {
    deleteStatusAuth(analysisUrl(`/${NON_EXISTENT_ID}`)).should('eq', 404);
  });

  it("DELETE /analysis/user-data returns HTTP 200 and clears the user's entire history", () => {
    createAnalysis('Bulk Delete A');
    createAnalysis('Bulk Delete B');
    deleteAllUserData().should('eq', 200);
    getJsonAuth(analysisUrl('/history')).should('have.length', 0);
  });

  it('DELETE /analysis/user-data returns HTTP 200 even when the user has no data', () => {
    deleteAllUserData();
    deleteAllUserData().should('eq', 200);
  });
});
