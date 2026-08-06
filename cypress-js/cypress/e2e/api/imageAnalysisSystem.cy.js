// System tests for the real image-analysis flow, mirroring selenium-java's
// TestApiImageAnalysisSystem.
//
// These tests require the SUT deployed with the analysis worker enabled and
// Ollama available (docker-compose.ollama-test.yml). Opt in explicitly with:
//   npm run test:image-analysis
// which passes --env REAL_OLLAMA_TESTS=true; otherwise the whole suite is
// registered as skipped (Mocha's describe.skip), mirroring the Java suite's
// Assumptions.assumeTrue(...) opt-in gate.
import { uploadImage, uploadWithoutFile, deleteAllUserData, waitForAnalysisTerminalStatus } from '../../support/apiClient';

const REAL_OLLAMA_TESTS = String(Cypress.env('REAL_OLLAMA_TESTS')) === 'true';
const maybeDescribe = REAL_OLLAMA_TESTS ? describe : describe.skip;

function hasNormalizedBox(cloudDetails) {
  if (!Array.isArray(cloudDetails)) return false;
  return cloudDetails.some((detail) => {
    const box = detail?.box;
    return Array.isArray(box) && box.length === 4 && box.every((value) => value >= 0 && value <= 1);
  });
}

function isNoCloudCompatible(results) {
  const cloudTypes = results?.cloudTypes;
  if (!cloudTypes || cloudTypes.length === 0) return true;
  return cloudTypes.includes('no_cloud');
}

function uploadAndAssertAnalyzing(imageKind, filename, contentType, location, includeExplainability) {
  return uploadImage({ imageKind, filename, contentType, location, includeExplainability }).then((response) => {
    expect(response.status).to.eq(200);
    expect(response.body).to.have.property('analysis_id');
    expect(response.body).to.have.property('status', 'analyzing');
    expect(response.body.analysis_id).to.be.greaterThan(0);
    return response.body;
  });
}

function waitForCompletedAnalysis(analysisId) {
  return waitForAnalysisTerminalStatus(analysisId).then((analysis) => {
    expect(analysis, `Analysis ${analysisId} must appear in history before timeout`).to.not.be.null;
    expect(analysis.status, `Analysis ${analysisId} unexpectedly cancelled - check the Ollama worker logs`).to.not.eq(
      'cancelled'
    );
    expect(analysis.status, `Analysis ${analysisId} must complete successfully`).to.eq('completed');
    return analysis;
  });
}

maybeDescribe('API: real image-analysis (Ollama)', () => {
  beforeEach(() => {
    deleteAllUserData();
  });

  it('BASE - Gallery/API JPG under 5 MB without explainability completes with cloud results', () => {
    uploadAndAssertAnalyzing('cloudy', 'base-gallery.jpg', 'image/jpeg', 'Base Gallery City', false).then((upload) => {
      waitForCompletedAnalysis(upload.analysis_id).then((completed) => {
        expect(completed.results.cloudTypes).to.not.be.empty;
      });
    });
  });

  it('2 - Camera-origin JPG is processed like a gallery upload', () => {
    uploadAndAssertAnalyzing('cloudy', 'camera-capture.jpg', 'image/jpeg', 'Camera City', false).then((upload) => {
      waitForCompletedAnalysis(upload.analysis_id).then((completed) => {
        expect(completed.status).to.eq('completed');
      });
    });
  });

  it('3 - Upload with no selected file is rejected', () => {
    uploadWithoutFile('No File City').its('status').should('eq', 422);
  });

  it('4 - Zero-byte image is rejected', () => {
    uploadImage({
      imageKind: 'empty',
      filename: 'empty.jpg',
      contentType: 'image/jpeg',
      location: 'Empty Image City',
      includeExplainability: false,
    })
      .its('status')
      .should('eq', 400);
  });

  it('5 - Image larger than 5 MB is rejected', () => {
    uploadImage({
      imageKind: 'tooLarge',
      filename: 'too-large.jpg',
      contentType: 'image/jpeg',
      location: 'Too Large City',
      includeExplainability: false,
    })
      .its('status')
      .should('eq', 413);
  });

  it('6 - Non-JPG upload is rejected', () => {
    uploadImage({
      imageKind: 'nonJpeg',
      filename: 'not-a-jpg.txt',
      contentType: 'text/plain',
      location: 'Wrong Format City',
      includeExplainability: false,
    })
      .its('status')
      .should('be.gte', 400);
  });

  it('7 - Explainability with clouds completes with normalized bounding boxes', () => {
    uploadAndAssertAnalyzing('cloudy', 'explainability-clouds.jpg', 'image/jpeg', 'Explainability City', true).then(
      (upload) => {
        waitForCompletedAnalysis(upload.analysis_id).then((completed) => {
          expect(hasNormalizedBox(completed.results.cloudDetails)).to.eq(true);
        });
      }
    );
  });

  it('8 - No-cloud JPG without explainability completes without boxes', () => {
    uploadAndAssertAnalyzing('noCloud', 'clear-sky.jpg', 'image/jpeg', 'Clear Sky City', false).then((upload) => {
      waitForCompletedAnalysis(upload.analysis_id).then((completed) => {
        expect(isNoCloudCompatible(completed.results)).to.eq(true);
        expect(hasNormalizedBox(completed.results.cloudDetails)).to.eq(false);
      });
    });
  });
});
