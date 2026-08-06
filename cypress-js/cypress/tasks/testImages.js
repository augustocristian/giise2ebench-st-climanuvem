// Pure Node helpers that synthesize the same JPEG fixtures selenium-java's
// BaseApiClass builds with java.awt.Graphics2D, but with jpeg-js over a raw
// RGBA buffer. Kept image-only (no HTTP) so analysisApi.js can reuse them.
const jpeg = require('jpeg-js');

function newBuffer(width, height) {
  return new Uint8Array(width * height * 4);
}

function setPixel(data, width, x, y, [r, g, b]) {
  if (x < 0 || y < 0 || x >= width) return;
  const offset = (y * width + x) * 4;
  data[offset] = r;
  data[offset + 1] = g;
  data[offset + 2] = b;
  data[offset + 3] = 255;
}

function fillRect(data, width, x0, y0, w, h, color) {
  for (let y = y0; y < y0 + h; y++) {
    for (let x = x0; x < x0 + w; x++) {
      setPixel(data, width, x, y, color);
    }
  }
}

function fillEllipse(data, width, height, cx, cy, rx, ry, color) {
  const top = Math.max(0, Math.floor(cy - ry));
  const bottom = Math.min(height, Math.ceil(cy + ry));
  for (let y = top; y < bottom; y++) {
    const dy = (y - cy) / ry;
    const spanSq = 1 - dy * dy;
    if (spanSq < 0) continue;
    const span = rx * Math.sqrt(spanSq);
    const left = Math.max(0, Math.round(cx - span));
    const right = Math.min(width, Math.round(cx + span));
    for (let x = left; x < right; x++) {
      setPixel(data, width, x, y, color);
    }
  }
}

function encode(data, width, height) {
  return jpeg.encode({ data, width, height }, 90).data;
}

/** Minimal 10x10 solid JPEG — small and fast, valid enough for the upload endpoint. */
function createTestImage() {
  const width = 10;
  const height = 10;
  const data = newBuffer(width, height);
  fillRect(data, width, 0, 0, width, height, [200, 200, 200]);
  return encode(data, width, height);
}

/** 640x360 blue sky with a handful of overlapping white/grey cloud ellipses. */
function createCloudyJpeg() {
  const width = 640;
  const height = 360;
  const data = newBuffer(width, height);
  fillRect(data, width, 0, 0, width, height, [98, 171, 232]);

  fillEllipse(data, width, height, 210, 142, 90, 47, [245, 248, 250]);
  fillEllipse(data, width, height, 340, 132, 105, 62, [245, 248, 250]);
  fillEllipse(data, width, height, 455, 155, 75, 40, [245, 248, 250]);
  fillRect(data, width, 175, 145, 310, 75, [245, 248, 250]);
  fillEllipse(data, width, height, 295, 202, 85, 27, [225, 232, 238]);

  return encode(data, width, height);
}

/** 640x360 clear vertical sky gradient — no clouds. */
function createNoCloudJpeg() {
  const width = 640;
  const height = 360;
  const data = newBuffer(width, height);

  for (let y = 0; y < height; y++) {
    const ratio = y / height;
    const r = 70 + Math.round(35 * ratio);
    const g = 155 + Math.round(45 * ratio);
    const b = 225 + Math.round(25 * ratio);
    for (let x = 0; x < width; x++) {
      setPixel(data, width, x, y, [r, g, b]);
    }
  }

  return encode(data, width, height);
}

function createEmptyImageBytes() {
  return Buffer.alloc(0);
}

/** A valid small JPEG followed by junk bytes, padded past the 5 MB upload limit. */
function createTooLargePayload() {
  const validJpeg = createTestImage();
  const size = 5 * 1024 * 1024 + 1;
  const payload = Buffer.alloc(size);
  validJpeg.copy(payload, 0);
  for (let i = validJpeg.length; i < size; i++) {
    payload[i] = i % 251;
  }
  return payload;
}

function createNonJpegPayload() {
  return Buffer.from('not-a-jpeg-image', 'utf8');
}

module.exports = {
  createTestImage,
  createCloudyJpeg,
  createNoCloudJpeg,
  createEmptyImageBytes,
  createTooLargePayload,
  createNonJpegPayload,
};
