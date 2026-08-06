// API spec for the analysis history endpoint, mirroring selenium-java's
// TestApiHistory:
//   GET /analysis/history — returns all analyses for the authenticated user
// A beforeEach cleanup ensures the test user starts with an empty history,
// making each scenario deterministic regardless of prior test runs.
import { deleteAllUserData, createAnalysis, getStatusAuth, getJsonAuth, analysisUrl, containsByField } from '../../support/apiClient';

describe('API: history', () => {
  beforeEach(() => {
    deleteAllUserData();
  });

  it('returns HTTP 200 with an empty list when the user has no analyses', () => {
    getStatusAuth(analysisUrl('/history')).should('eq', 200);
    getJsonAuth(analysisUrl('/history')).should('have.length', 0);
  });

  it('returns HTTP 200 and lists the uploaded analysis', () => {
    createAnalysis('Oviedo, Spain').then((analysisId) => {
      getJsonAuth(analysisUrl('/history')).then((history) => {
        expect(history).to.not.be.empty;
        expect(containsByField(history, 'id', analysisId)).to.eq(true);
      });
    });
  });

  it('returns entries with id, status, date, location, imageUrl, and results', () => {
    createAnalysis('Test City');
    getJsonAuth(analysisUrl('/history')).then((history) => {
      expect(history).to.not.be.empty;
      const entry = history[0];
      ['id', 'status', 'date', 'location', 'imageUrl', 'results'].forEach((field) => {
        expect(entry).to.have.property(field);
      });
    });
  });

  it('results block contains cloudTypes, cloudDetails, forecast, and warnings', () => {
    createAnalysis('Results Field City');
    getJsonAuth(analysisUrl('/history')).then((history) => {
      expect(history).to.not.be.empty;
      const { results } = history[0];
      ['cloudTypes', 'cloudDetails', 'forecast', 'warnings'].forEach((field) => {
        expect(results).to.have.property(field);
      });
    });
  });
});
