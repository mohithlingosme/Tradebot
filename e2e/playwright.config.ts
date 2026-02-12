import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60 * 1000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:4173',
    trace: 'on-first-retry',
    video: 'on',
    screenshot: 'only-on-failure',
  },
  reporter: [['list'], ['html', { outputFolder: 'artifacts/playwright' }]],
});
