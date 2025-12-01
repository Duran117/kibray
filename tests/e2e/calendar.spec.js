import { test, expect } from '@playwright/test';

test.describe('Calendar', () => {
  test('navigate to calendar', async ({ page }) => {
    await page.goto('/calendar');
    await expect(page.locator('text=/january|february|march|april|may|june|july|august|september|october|november|december/i')).toBeVisible();
  });
});
