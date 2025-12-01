import { test, expect } from '@playwright/test';

test.describe('Reports', () => {
  test('navigate and see generator', async ({ page }) => {
    await page.goto('/reports');
    await expect(page.getByText(/report generator/i)).toBeVisible();
  });
});
