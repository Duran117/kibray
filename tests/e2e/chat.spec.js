import { test, expect } from '@playwright/test';

test.describe('Chat', () => {
  test('navigate to chat', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.getByText(/team chat/i)).toBeVisible();
  });
});
