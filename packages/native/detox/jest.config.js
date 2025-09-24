module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/detox/setup.ts'],
  testMatch: ['<rootDir>/**/*.e2e.ts'],
  verbose: true,
};
