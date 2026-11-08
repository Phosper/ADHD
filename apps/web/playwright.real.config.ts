import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'real.spec.ts', workers: 1, timeout: 180000,
  outputDir: '../../runtime/real-browser-results',
  use: { baseURL: 'http://127.0.0.1:18093', channel: 'chrome',
    permissions: ['microphone'], launchOptions: { args: ['--use-fake-ui-for-media-stream'] } },
  webServer: { command: 'node tests/start-real.mjs', url: 'http://127.0.0.1:18093/health', timeout: 60000 },
});
