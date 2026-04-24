import { test, expect } from '@playwright/test';

test.describe('Global Search', () => {
  test('open with keyboard and search', async ({ page }) => {
    await page.goto('/files'); // Go to working route
    // Wait for React mount via network-idle instead of fixed 2s sleep.
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

    // GlobalSearch component should be in DOM (even if not visible)
    const globalSearch = page.locator('[data-testid="global-search"]');

    // Open global search with Cmd+K — visibility assertion below has its own
    // timeout, no need for an arbitrary post-keypress sleep.
    await page.keyboard.press('Meta+k');

    // After Cmd+K, the modal should be visible
    await expect(globalSearch).toBeVisible({ timeout: 5000 });
  });
});
