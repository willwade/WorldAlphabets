module.exports = {
  testMatch: [
    '<rootDir>/__tests__/**/*.test.js',
    '<rootDir>/tests/**/*.test.js',
    '<rootDir>/packages/js/tests/**/*.test.ts'
  ],
  transform: {
    '^.+\\.ts$': ['ts-jest', { tsconfig: '<rootDir>/packages/js/tsconfig.json' }]
  }
};
