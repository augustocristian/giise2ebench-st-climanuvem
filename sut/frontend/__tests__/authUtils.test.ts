import { EMAIL_REGEX, getAuthErrorMessage } from '@/src/utils/authUtils';

describe('authUtils', () => {
  it('validates common email formats', () => {
    expect(EMAIL_REGEX.test('user@example.com')).toBe(true);
    expect(EMAIL_REGEX.test('bad-email')).toBe(false);
  });

  it('returns a friendly message for known Firebase errors', () => {
    expect(getAuthErrorMessage('auth/invalid-credential')).toBeTruthy();
    expect(getAuthErrorMessage('auth/invalid-credential')).not.toContain('auth/invalid-credential');
  });

  it('falls back to the default translated error with the original code', () => {
    expect(getAuthErrorMessage('auth/unknown-test-code')).toContain('auth/unknown-test-code');
  });
});
