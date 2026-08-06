import { formatDate, getStatusColor, getStatusText, getWarningLevelColor } from '@/src/utils/statusUtils';

const theme = {
  colors: {
    success: '#00aa00',
    primary: '#0066ff',
    danger: '#cc0000',
    textSecondary: '#666666',
    warning: '#ffaa00',
  },
  mode: 'light',
};

describe('statusUtils', () => {
  it('maps known statuses to theme colors', () => {
    expect(getStatusColor('completed', theme as any)).toBe('#00aa00');
    expect(getStatusColor('analyzing', theme as any)).toBe('#0066ff');
    expect(getStatusColor('cancelled', theme as any)).toBe('#cc0000');
  });

  it('falls back to secondary text color for unknown statuses', () => {
    expect(getStatusColor('queued', theme as any)).toBe('#666666');
  });

  it('capitalizes status text and preserves empty values', () => {
    expect(getStatusText('completed')).toBe('Completed');
    expect(getStatusText('')).toBe('');
  });

  it('maps warning levels to theme colors', () => {
    expect(getWarningLevelColor(0, theme as any)).toBe('#666666');
    expect(getWarningLevelColor(1, theme as any)).toBe('#ffaa00');
    expect(getWarningLevelColor(2, theme as any)).toBe('#cc0000');
    expect(getWarningLevelColor(3, theme as any)).toBe('#B71C1C');
  });

  it('formats dates using the selected language', () => {
    expect(formatDate('2026-07-05T17:45:00.000Z', 'es')).toContain('05/07/2026');
    expect(formatDate('2026-07-05T17:45:00.000Z', 'en')).toContain('07/05/2026');
  });

  it('formats invalid dates using the platform fallback', () => {
    expect(formatDate('not-a-date', 'en')).toBe('Invalid Date');
  });
});
