import BasePage from './BasePage';

const CAMERA_CARD_TEXT = 'Take Photo';
const GALLERY_CARD_TEXT = 'Gallery';
const EXPLAINABILITY_TEXT = 'Explainability';
const FORMATS_INFO_TEXT = 'Supported formats';
const PAGE_HEADER_TEXT = 'Analyze Image';

/**
 * Page Object for the Capture (image-upload) screen. Constructing this
 * object waits until the "Take Photo" card is visible.
 */
export default class CapturePage extends BasePage {
  constructor() {
    super();
    this.byPartialText(CAMERA_CARD_TEXT).should('be.visible');
  }

  // ── Assertions ────────────────────────────────────────────────────────────

  assertCameraOptionVisible() {
    this.byPartialText(CAMERA_CARD_TEXT).should('be.visible');
    return this;
  }

  assertGalleryOptionVisible() {
    this.byPartialText(GALLERY_CARD_TEXT).should('be.visible');
    return this;
  }

  assertExplainabilityVisible() {
    this.byPartialText(EXPLAINABILITY_TEXT).should('be.visible');
    return this;
  }

  assertFormatsInfoVisible() {
    this.byPartialText(FORMATS_INFO_TEXT).should('be.visible');
    return this;
  }

  assertPageHeaderVisible() {
    this.byPartialText(PAGE_HEADER_TEXT).should('be.visible');
    return this;
  }
}
