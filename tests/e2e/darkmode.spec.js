import { test, expect } from '@playwright/test';

test.describe('Dark Mode', () => {
  test('toggle dark mode', async ({ page }) => {
    await page.goto('/');
    const toggle = page.locator('button:has-text("Theme")');
    if ((await toggle.count()) === 0) {
      test.skip(true, 'Theme toggle not present in current shell');
      return;
    }
    await toggle.first().click();
    await page.waitForTimeout(500);
    const bodyClass = await page.locator('body').getAttribute('class');
    expect(bodyClass || '').toContain('dark');
  });
});
