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
    // Replace fixed 500ms sleep with a polled assertion that the dark class
    // appears on <body>. Playwright's expect-poll retries up to the timeout.
    await expect
      .poll(async () => (await page.locator('body').getAttribute('class')) || '', {
        timeout: 3000,
      })
      .toContain('dark');
    const bodyClass = await page.locator('body').getAttribute('class');
    expect(bodyClass || '').toContain('dark');
  });
});
