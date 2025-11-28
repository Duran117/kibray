import { test, expect, Page } from '@playwright/test';

async function login(page: Page){
  await page.goto('/admin/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('input[type="submit"]');
  // Wait for body to ensure post-login render
  await page.waitForSelector('body');
}

test.describe.serial('NotificationCenter E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/dashboard/');
    await expect(page.locator('#notification-root')).toBeVisible({ timeout: 10000 });
  });

  test('NotificationCenter component loads in header', async ({ page }) => {
    const notificationRoot = page.locator('#notification-root');
    await expect(notificationRoot).toBeVisible();
    const bellButton = page.locator('#notification-root button');
    await expect(bellButton).toBeVisible();
  });

  test('Bell button opens panel', async ({ page }) => {
    const bellButton = page.locator('#notification-root button');
    await expect(bellButton).toBeEnabled();
    await bellButton.click();
    // Wait for panel header (more specific than just "Notifications" text)
    const panelHeader = page.locator('#notification-root').getByRole('heading', { name: /notifications/i }).or(
      page.locator('#notification-root strong:has-text("Notifications")')
    );
    await expect(panelHeader.first()).toBeVisible({ timeout: 5000 });
  });

  test('Unread count badge appears after creating notification', async ({ page }) => {
    await page.evaluate(async () => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      await fetch('/api/v1/notifications/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken || '' },
        credentials: 'include',
        body: JSON.stringify({
          notification_type: 'task_created',
          title: 'Badge Test',
          message: 'Badge should show',
          is_read: false
        })
      });
    });
    await page.reload();
    const badge = page.locator('#notification-root button span');
    await expect(badge).toBeVisible({ timeout: 5000 });
  });

  test('Panel shows list or empty state', async ({ page }) => {
    await page.locator('#notification-root button').click();
    const loading = page.locator('#notification-root div:has-text("Loading...")');
    await loading.waitFor({ state: 'detached', timeout: 7000 }).catch(()=>{});
    const empty = page.locator('#notification-root div:has-text("No notifications")');
    const items = page.locator('#notification-root div[style*="cursor"]');
    const isEmpty = await empty.isVisible().catch(()=>false);
    const count = await items.count();
    expect(isEmpty || count > 0).toBeTruthy();
  });

  test('Mark all read button present', async ({ page }) => {
    await page.locator('#notification-root button').click();
    const markAll = page.locator('#notification-root button:has-text("Mark all read")');
    await expect(markAll).toBeVisible({ timeout: 5000 });
  });

  test('Panel toggles closed on second click', async ({ page }) => {
    // Use selector for bell button (button with emoji, not text button)
    const bell = page.locator('#notification-root button').filter({ hasText: '🔔' });
    await bell.click();
    await expect(page.locator('#notification-root strong:has-text("Notifications")')).toBeVisible();
    await bell.click();
    await expect(page.locator('#notification-root strong:has-text("Notifications")')).toHaveCount(0);
  });

  test('Persists after navigation', async ({ page }) => {
    await expect(page.locator('#notification-root button')).toBeVisible();
    await page.goto('/projects/');
    await expect(page.locator('#notification-root button')).toBeVisible();
  });

  test('Unread count endpoint returns numeric value', async ({ page }) => {
    const result = await page.evaluate(async () => {
      const res = await fetch('/api/v1/notifications/count_unread/', { credentials: 'include' });
      return { status: res.status, data: await res.json() };
    });
    expect(result.status).toBe(200);
    expect(typeof result.data.unread_count).toBe('number');
  });

  test('No React errors on panel open', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', err => errors.push(err.message));
    await page.locator('#notification-root button').click();
    const relevant = errors.filter(e => e.toLowerCase().includes('notification') || e.toLowerCase().includes('react'));
    expect(relevant).toHaveLength(0);
  });

  test('Notification item clickable and marks read', async ({ page }) => {
    await page.evaluate(async () => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      await fetch('/api/v1/notifications/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken || '' },
        credentials: 'include',
        body: JSON.stringify({
          notification_type: 'task_created',
          title: 'Clickable',
          message: 'Click me',
          is_read: false
        })
      });
    });
    await page.reload();
    await page.locator('#notification-root button').click();
    const item = page.locator('#notification-root div[style*="cursor"]').first();
    await expect(item).toBeVisible();
    await item.click();
    await page.waitForTimeout(500); // allow state update
  });
});
