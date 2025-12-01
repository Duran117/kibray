// @ts-check
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 3,
  reporter: [ ['list'], ['html', { open: 'never' }] ],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /auth\.setup\.js/,
      // Setup project should NOT use storageState since it's creating it
    },
    {
      name: 'chromium',
      use: { 
        browserName: 'chromium',
        storageState: 'auth.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { 
        browserName: 'firefox',
        storageState: 'auth.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: { 
        browserName: 'webkit',
        storageState: 'auth.json',
      },
      dependencies: ['setup'],
    },
  ],
  webServer: {
    command: 'python3 manage.py runserver',
    url: 'http://localhost:8000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
