import { test, expect } from '@playwright/test';

test.describe('Global Search', () => {
  test('open with keyboard and search', async ({ page }) => {
    await page.goto('/files'); // Go to working route
    await page.waitForTimeout(2000); // Wait for React to mount
    
    // GlobalSearch component should be in DOM (even if not visible)
    const globalSearch = page.locator('[data-testid="global-search"]');
    
    // Open global search with Cmd+K
    await page.keyboard.press('Meta+k');
    await page.waitForTimeout(1000);
    
    // After Cmd+K, the modal should be visible
    await expect(globalSearch).toBeVisible({ timeout: 5000 });
  });
});
