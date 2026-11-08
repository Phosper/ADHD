import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'voice.spec.ts', workers: 1, timeout: 45000,
  outputDir: '../../runtime/voice-browser-results',
  use: { baseURL: 'http://127.0.0.1:18091', channel: 'chrome',
    permissions: ['microphone'], launchOptions: { args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] } },
  webServer: { command: 'node tests/start-voice.mjs', url: 'http://127.0.0.1:18091/health', timeout: 60000 },
});
