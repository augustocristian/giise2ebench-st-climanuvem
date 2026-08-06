module.exports = {
  preset: 'jest-expo',
  moduleNameMapper: {
    '^@/src/config/firebaseConfig$': '<rootDir>/__tests__/mocks/firebaseConfigMock.ts',
    '^@/src/services/LoggerService$': '<rootDir>/__tests__/mocks/LoggerServiceMock.ts',
    '^@/(.*)$': '<rootDir>/$1',
  },
  testMatch: ['**/__tests__/**/*.(test|spec).(ts|tsx|js)'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  coverageReporters: ['text', 'lcov'],
  collectCoverageFrom: [
    'src/services/**/*.{ts,tsx}',
    'src/utils/**/*.{ts,tsx}',
    '!**/__tests__/**',
    '!**/mocks/**',
    '!src/services/AuthService.ts',
    '!src/services/LoggerService.ts',
    '!src/services/NotificationService.ts',
    '!src/services/mockData.ts',
    '!src/utils/captureUtils.ts',
    '!**/*.d.ts',
  ],
};
