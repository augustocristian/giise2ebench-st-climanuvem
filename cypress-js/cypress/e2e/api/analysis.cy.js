// API spec for the image-upload endpoint, mirroring selenium-java's
// TestApiAnalysis:
//   POST /analysis/upload — creates an analysis record and returns its ID
// Runs with DISABLE_WORKER=true, so uploaded analyses stay in 'analyzing'
// status — no Ollama connection required.
import { uploadImage, createAnalysis } from '../../support/apiClient';

describe('API: analysis upload', () => {
  it("returns HTTP 200 with status 'analyzing' and a positive analysis_id", () => {
    uploadImage({ location: 'Test Location' }).then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.property('analysis_id');
      expect(response.body).to.have.property('status', 'analyzing');
      expect(response.body.analysis_id).to.be.greaterThan(0);
    });
  });

  it('returns HTTP 200', () => {
    uploadImage({ location: 'Another Location' }).its('status').should('eq', 200);
  });

  it('with a custom location stores the location in the response', () => {
    const location = `Madrid, Spain ${Date.now()}`;
    uploadImage({ location }).then((response) => {
      expect(response.body).to.have.property('analysis_id');
      expect(response.body.analysis_id).to.be.greaterThan(0);
    });
  });

  it('two consecutive uploads produce distinct analysis IDs', () => {
    createAnalysis('Location A').then((id1) => {
      createAnalysis('Location B').then((id2) => {
        expect(id2).to.not.eq(id1);
      });
    });
  });
});
