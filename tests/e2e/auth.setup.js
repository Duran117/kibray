import { test as setup } from '@playwright/test';

/**
 * Global auth setup: saves storage state to auth.json
 */
setup('authenticate', async ({ page, context }) => {
  // Navigate and bypass login by setting token directly
  await page.goto('/');
  
  await page.evaluate(() => {
    localStorage.setItem('authToken', 'test-auth-token-for-e2e-testing');
  });
  
  // Save authenticated state
  await context.storageState({ path: 'auth.json' });
});
