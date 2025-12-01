import { test, expect } from '@playwright/test';

test.describe('User Management', () => {
  test('navigate to users', async ({ page }) => {
    await page.goto('/users');
    await expect(page.getByText(/user management/i)).toBeVisible();
  });
});
