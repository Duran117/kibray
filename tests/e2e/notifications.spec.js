import { test, expect } from '@playwright/test';

test.describe('Notifications', () => {
  test('bell icon displays', async ({ page }) => {
    await page.goto('/files'); // Go to working route
    // Wait for React mount via network-idle instead of fixed 2s sleep.
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    // Check if notification component renders (it's in MainLayout)
    const notificationElement = page.locator('[data-testid="notification-center"]');
    await expect(notificationElement).toBeVisible({ timeout: 5000 });
  });
});
