const detox = require('detox');
const config = require('../detox.config');

beforeAll(async () => {
  await detox.init(config);
});

afterAll(async () => {
  await detox.cleanup();
});
