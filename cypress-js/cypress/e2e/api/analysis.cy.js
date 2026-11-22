// API spec for the image-upload endpoint, mirroring selenium-java's
// TestApiAnalysis:
//   POST /api/v1/analyses — creates an analysis record (202 Accepted)
// Runs with DISABLE_WORKER=true, so uploaded analyses stay in 'analyzing'
// status — no Ollama connection required.
import { uploadImage, createAnalysis, getAuth, analysisUrl } from '../../support/apiClient';

describe('API: analysis upload', () => {
  it("returns HTTP 202 with status 'analyzing' and a positive integer id", () => {
    uploadImage({ location: 'Test Location' }).then((response) => {
      expect(response.status).to.eq(202);
      expect(response.body).to.have.property('status', 'analyzing');
      expect(response.body.id).to.be.a('number');
      expect(response.body.id).to.be.greaterThan(0);
      expect(response.body).to.not.have.property('analysis_id');
    });
  });

  it('returns a Location header pointing at the new analysis', () => {
    uploadImage({ location: 'Another Location' }).then((response) => {
      expect(response.headers.location).to.match(new RegExp(`/api/v1/analyses/${response.body.id}$`));
    });
  });

  it('the new analysis is retrievable and keeps the custom location', () => {
    const location = `Madrid, Spain ${Date.now()}`;
    uploadImage({ location }).then((response) => {
      getAuth(analysisUrl(`/${response.body.id}`)).then((got) => {
        expect(got.status).to.eq(200);
        expect(got.body).to.have.property('location', location);
      });
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
