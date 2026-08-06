// Node-side tasks registered with Cypress in cypress.config.js.
//
// Cypress's own cy.request() only builds application/x-www-form-urlencoded
// bodies, so multipart image upload (and JPEG synthesis, which needs jpeg-js)
// happen here in the Node process instead — mirroring how selenium-java's
// BaseApiClass built multipart requests with Apache HttpClient, just on the
// Node side of the Cypress task boundary rather than inline in the spec.
const axios = require('axios');
const FormData = require('form-data');
const testImages = require('./testImages');

const IMAGE_BUILDERS = {
  test: testImages.createTestImage,
  cloudy: testImages.createCloudyJpeg,
  noCloud: testImages.createNoCloudJpeg,
  empty: testImages.createEmptyImageBytes,
  tooLarge: testImages.createTooLargePayload,
  nonJpeg: testImages.createNonJpegPayload,
};

function parseBody(rawData) {
  if (Buffer.isBuffer(rawData)) {
    const text = rawData.toString('utf8');
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
  return rawData;
}

async function toApiResponse(promise) {
  try {
    const response = await promise;
    return { status: response.status, body: parseBody(response.data) };
  } catch (error) {
    if (error.response) {
      return { status: error.response.status, body: parseBody(error.response.data) };
    }
    throw error;
  }
}

/**
 * Uploads a synthesized or literal image to POST /analysis/upload (or any
 * given URL) as multipart/form-data. `imageKind` selects a fixture from
 * testImages.js; pass `imageBase64` instead to upload arbitrary bytes.
 */
function uploadImage({
  url,
  token,
  location,
  imageKind,
  imageBase64,
  filename = 'test.jpg',
  contentType = 'image/jpeg',
  includeExplainability,
}) {
  const bytes = imageBase64 ? Buffer.from(imageBase64, 'base64') : IMAGE_BUILDERS[imageKind]();

  const form = new FormData();
  form.append('file', bytes, { filename, contentType });
  form.append('location', location);
  if (includeExplainability !== undefined) {
    form.append('include_explainability', String(includeExplainability));
  }

  return toApiResponse(
    axios.post(url, form, {
      headers: { ...form.getHeaders(), Authorization: `Bearer ${token}` },
      validateStatus: () => true,
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
    })
  );
}

/** Multipart POST with only the `location` field — no `file` part at all. */
function uploadWithoutFile({ url, token, location }) {
  const form = new FormData();
  form.append('location', location);

  return toApiResponse(
    axios.post(url, form, {
      headers: { ...form.getHeaders(), Authorization: `Bearer ${token}` },
      validateStatus: () => true,
    })
  );
}

/**
 * Signs in with Firebase Auth REST and deletes the resulting account.
 * Mirrors BaseLoggedClass#deleteFirebaseAccountIfConfigured: best-effort
 * cleanup for the unique account TestRegisterSystem/register.cy.js creates.
 */
async function deleteFirebaseAccount({ apiKey, email, password }) {
  if (!apiKey) {
    console.warn(`[analysisApi] Skipping Firebase cleanup for ${email}: no FIREBASE_WEB_API_KEY configured`);
    return false;
  }

  try {
    const signIn = await axios.post(
      `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${apiKey}`,
      { email, password, returnSecureToken: true }
    );
    const idToken = signIn.data.idToken;

    await axios.post(`https://identitytoolkit.googleapis.com/v1/accounts:delete?key=${apiKey}`, { idToken });
    console.log(`[analysisApi] Deleted Firebase account created during test: ${email}`);
    return true;
  } catch (error) {
    console.warn(`[analysisApi] Could not delete Firebase account ${email}:`, error.message);
    return false;
  }
}

module.exports = { uploadImage, uploadWithoutFile, deleteFirebaseAccount };
