const mockFiles: Record<string, { exists: boolean; size?: number }> = {};
const mockRequestForegroundPermissionsAsync = jest.fn();
const mockGetCurrentPositionAsync = jest.fn();
const mockReverseGeocodeAsync = jest.fn();
const mockManipulate = jest.fn();
const mockGetPushTokenAsync = jest.fn();

jest.mock('expo-file-system', () => ({
  __esModule: true,
  File: jest.fn().mockImplementation((uri: string) => ({
    exists: mockFiles[uri]?.exists ?? false,
    info: jest.fn(() => ({ size: mockFiles[uri]?.size })),
  })),
}));

jest.mock('expo-location', () => ({
  __esModule: true,
  Accuracy: { Balanced: 'balanced' },
  requestForegroundPermissionsAsync: mockRequestForegroundPermissionsAsync,
  getCurrentPositionAsync: mockGetCurrentPositionAsync,
  reverseGeocodeAsync: mockReverseGeocodeAsync,
}));

jest.mock('expo-image-manipulator', () => ({
  __esModule: true,
  ImageManipulator: { manipulate: mockManipulate },
  SaveFormat: { JPEG: 'jpeg' },
}));

jest.mock('@/src/services/NotificationService', () => ({
  __esModule: true,
  NotificationService: {
    getPushTokenAsync: mockGetPushTokenAsync,
  },
}));

import {
  getFCMToken,
  getImageSize,
  getLocationData,
  optimizeImage,
  validateIsJpg,
} from '@/src/utils/captureUtils';

const translations = {
  unknownLocation: 'Unknown location',
  unknownCity: 'Unknown city',
  unknownCountry: 'Unknown country',
};

describe('captureUtils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Object.keys(mockFiles).forEach((key) => delete mockFiles[key]);
  });

  it('validates JPG and JPEG extensions case-insensitively', () => {
    expect(validateIsJpg('file:///tmp/cloud.JPG')).toBe(true);
    expect(validateIsJpg('file:///tmp/cloud.jpeg')).toBe(true);
    expect(validateIsJpg('file:///tmp/cloud.png')).toBe(false);
  });

  it('returns image size when the file exists', () => {
    mockFiles['file:///tmp/cloud.jpg'] = { exists: true, size: 1234 };

    expect(getImageSize('file:///tmp/cloud.jpg')).toBe(1234);
  });

  it('returns null when the file does not exist', () => {
    expect(getImageSize('file:///tmp/missing.jpg')).toBeNull();
  });

  it('returns unknown location when permission is denied', async () => {
    mockRequestForegroundPermissionsAsync.mockResolvedValue({ status: 'denied' });

    await expect(getLocationData(translations)).resolves.toEqual({
      locationStr: 'Unknown location',
      latitude: undefined,
      longitude: undefined,
    });
  });

  it('returns undefined when notifications fail', async () => {
    mockGetPushTokenAsync.mockRejectedValue(new Error('notification error'));

    await expect(getFCMToken()).resolves.toBeUndefined();
  });

  it('returns the original image when optimization fails', async () => {
    mockManipulate.mockImplementation(() => {
      throw new Error('manipulator failed');
    });

    await expect(optimizeImage('file:///tmp/cloud.jpg')).resolves.toBe('file:///tmp/cloud.jpg');
  });
});
