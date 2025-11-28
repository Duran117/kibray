import { defineConfig, devices } from '@playwright/test';

// Playwright configuration for Django + React integration tests
// - Starts Django automatically (webServer) unless already running
// - Uses baseURL so tests can use relative paths
// - Disables full parallelism for stability with a single shared DB
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Ensure deterministic execution with shared state
  reporter: [['html'], ['list']],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ],
  webServer: {
    command: '/Users/jesus/Documents/kibray/.venv/bin/python ../manage.py runserver 8000',
    port: 8000,
    timeout: 120_000,
    reuseExistingServer: true
  }
});
