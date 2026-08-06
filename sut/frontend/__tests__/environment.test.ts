import { isTestMode } from '@/src/utils/environment';

describe('environment', () => {
  const originalTestMode = process.env.EXPO_PUBLIC_TEST_MODE;

  afterEach(() => {
    process.env.EXPO_PUBLIC_TEST_MODE = originalTestMode;
  });

  it('detects explicit test mode', () => {
    process.env.EXPO_PUBLIC_TEST_MODE = 'true';
    expect(isTestMode()).toBe(true);
  });

  it('treats every other value as non-test mode', () => {
    process.env.EXPO_PUBLIC_TEST_MODE = 'false';
    expect(isTestMode()).toBe(false);
  });
});
