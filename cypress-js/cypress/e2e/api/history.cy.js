// API spec for the analysis collection/single GET endpoints, mirroring
// selenium-java's TestApiHistory:
//   GET /api/v1/analyses       — analyses of the authenticated user (newest first),
//                                paginated with `page`/`size`, total in X-Total-Count
//   GET /api/v1/analyses/{id}  — one analysis (200) or 404 ANALYSIS_NOT_FOUND
//   GET /api/v1/analyses/{id}/image — authenticated JPEG of the analysis
// A beforeEach cleanup ensures the test user starts with an empty history,
// making each scenario deterministic regardless of prior test runs.
import { deleteAllUserData, createAnalysis, getAuth, requestAuth, getStatusAuth, getJsonAuth, expectProblem, expectAllowIncludes, analysisUrl, containsByField, getBinaryAuth, requestNoAuth, legacyUrl } from '../../support/apiClient';

const NON_EXISTENT_ID = 2147483647;

describe('API: history', () => {
  beforeEach(() => {
    deleteAllUserData();
  });

  it('returns HTTP 200 with an empty list when the user has no analyses', () => {
    getStatusAuth(analysisUrl('')).should('eq', 200);
    getJsonAuth(analysisUrl('')).should('have.length', 0);
  });

  it('returns HTTP 200 and lists the uploaded analysis', () => {
    createAnalysis('Oviedo, Spain').then((analysisId) => {
      getJsonAuth(analysisUrl('')).then((history) => {
        expect(history).to.not.be.empty;
        expect(containsByField(history, 'id', analysisId)).to.eq(true);
      });
    });
  });

  it('returns entries with id, status, date, location, imageUrl, and results', () => {
    createAnalysis('Test City');
    getJsonAuth(analysisUrl('')).then((history) => {
      expect(history).to.not.be.empty;
      const entry = history[0];
      ['id', 'status', 'date', 'location', 'imageUrl', 'results'].forEach((field) => {
        expect(entry).to.have.property(field);
      });
      expect(entry.id).to.be.a('number');
      expect(entry.date).to.match(/Z$/);
    });
  });

  it('results block contains cloudTypes, cloudDetails, forecast, and warnings', () => {
    createAnalysis('Results Field City');
    getJsonAuth(analysisUrl('')).then((history) => {
      expect(history).to.not.be.empty;
      const { results } = history[0];
      ['cloudTypes', 'cloudDetails', 'forecast', 'warnings'].forEach((field) => {
        expect(results).to.have.property(field);
      });
    });
  });

  it('paginates with page and size and reports the total in X-Total-Count', () => {
    createAnalysis('Page A');
    createAnalysis('Page B');
    createAnalysis('Page C');
    getAuth(`${analysisUrl('')}?page=0&size=2`).then((first) => {
      expect(first.status).to.eq(200);
      expect(first.body).to.have.length(2);
      expect(Number(first.headers['x-total-count'])).to.eq(3);
    });
    getAuth(`${analysisUrl('')}?page=1&size=2`).then((second) => {
      expect(second.body).to.have.length(1);
      expect(Number(second.headers['x-total-count'])).to.eq(3);
    });
  });

  it('rejects an out-of-range page size with HTTP 422', () => {
    getStatusAuth(`${analysisUrl('')}?size=101`).should('eq', 422);
  });

  it('GET /api/v1/analyses/{id} returns HTTP 200 with the analysis', () => {
    createAnalysis('Single City').then((analysisId) => {
      getAuth(analysisUrl(`/${analysisId}`)).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('id', analysisId);
        expect(response.body).to.have.property('location', 'Single City');
        expect(response.body).to.have.property('results');
      });
    });
  });

  it('GET /api/v1/analyses/{id} returns HTTP 404 ANALYSIS_NOT_FOUND for a non-existent analysis', () => {
    getAuth(analysisUrl(`/${NON_EXISTENT_ID}`)).then((response) =>
      expectProblem(response, 404, 'ANALYSIS_NOT_FOUND')
    );
  });

  it('PUT /api/v1/analyses is not allowed: HTTP 405 with Allow: GET, POST, DELETE', () => {
    requestAuth('PUT', analysisUrl('')).then((response) =>
      expectAllowIncludes(response, ['GET', 'POST', 'DELETE'])
    );
  });

  it('imageUrl is the relative path /api/v1/analyses/{id}/image', () => {
    createAnalysis('Image Url City').then((analysisId) => {
      getAuth(analysisUrl(`/${analysisId}`)).then((response) => {
        expect(response.body).to.have.property('imageUrl', `/api/v1/analyses/${analysisId}/image`);
      });
    });
  });

  it('GET /api/v1/analyses/{id}/image returns the JPEG for its owner', () => {
    createAnalysis('Image Owner City').then((analysisId) => {
      getBinaryAuth(analysisUrl(`/${analysisId}/image`)).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.headers['content-type']).to.include('image/jpeg');
        const body = String(response.body);
        expect(body.length).to.be.greaterThan(3);
        expect([0, 1, 2].map((i) => body.charCodeAt(i) & 0xff)).to.deep.eq([0xff, 0xd8, 0xff]);
      });
    });
  });

  it('GET /api/v1/analyses/{id}/image without Authorization returns HTTP 401 NOT_AUTHENTICATED', () => {
    createAnalysis('Image NoAuth City').then((analysisId) => {
      requestNoAuth('GET', analysisUrl(`/${analysisId}/image`)).then((response) =>
        expectProblem(response, 401, 'NOT_AUTHENTICATED')
      );
    });
  });

  it('GET /api/v1/analyses/{id}/image returns HTTP 404 ANALYSIS_NOT_FOUND for an unknown id', () => {
    getAuth(analysisUrl(`/${NON_EXISTENT_ID}/image`)).then((response) =>
      expectProblem(response, 404, 'ANALYSIS_NOT_FOUND')
    );
  });

  it('the public /uploads mount no longer exists: GET /uploads/anything.jpg returns HTTP 404', () => {
    requestNoAuth('GET', legacyUrl('/uploads/anything.jpg')).its('status').should('eq', 404);
  });
});
