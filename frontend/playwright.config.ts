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
    // Override Python interpreter via PYTHON env var (defaults to python3 on PATH).
    // Override server port via DJANGO_PORT (defaults to 8000).
    command: `${process.env.PYTHON ?? 'python3'} ../manage.py runserver ${process.env.DJANGO_PORT ?? '8000'}`,
    port: Number(process.env.DJANGO_PORT ?? '8000'),
    timeout: 120_000,
    reuseExistingServer: true
  }
});
