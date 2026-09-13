const path = require('node:path');

// jest-expo's setup requires `expo-modules-core` directly, but npm nests it under
// expo/node_modules rather than hoisting it (a peer-dependency conflict on
// react-native-worklets prevents hoisting to the top level). Add expo's own
// node_modules as a module lookup directory so Jest can still resolve it.
const expoNodeModules = path.join(path.dirname(require.resolve('expo/package.json')), 'node_modules');

module.exports = {
  preset: 'jest-expo',
  moduleDirectories: ['node_modules', expoNodeModules],
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
