import { test, expect } from '@playwright/test';

test.describe('Dark Mode', () => {
  test('toggle dark mode', async ({ page }) => {
    await page.goto('/');
    const toggle = page.locator('button:has-text("Theme")');
    if (await toggle.count()) {
      await toggle.first().click();
      await page.waitForTimeout(500);
      const bodyClass = await page.locator('body').getAttribute('class');
      expect(bodyClass || '').toContain('dark');
    }
  });
});
