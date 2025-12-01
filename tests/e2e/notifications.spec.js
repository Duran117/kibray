import { test, expect } from '@playwright/test';

test.describe('Notifications', () => {
  test('bell icon displays', async ({ page }) => {
    await page.goto('/files'); // Go to working route
    await page.waitForTimeout(2000); // Wait for React to mount
    // Check if notification component renders (it's in MainLayout)
    const notificationElement = page.locator('[data-testid="notification-center"]');
    await expect(notificationElement).toBeVisible({ timeout: 5000 });
  });
});
