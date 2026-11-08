import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: 'console.spec.ts',
  outputDir: '../../runtime/browser-results',
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:18090', channel: process.env.CI ? 'chromium' : 'chrome', screenshot: 'only-on-failure' },
  webServer: {
    command: 'node tests/start-api.mjs',
    url: 'http://127.0.0.1:18090/health',
    reuseExistingServer: false,
  },
});
