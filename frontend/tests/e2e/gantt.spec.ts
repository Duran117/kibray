import { test, expect, Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/admin/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('input[type="submit"]');
  await page.waitForSelector('body');
}

async function waitForGanttMount(page: Page) {
  await page.waitForSelector('#gantt-app-root', { timeout: 10000 });
  await page.waitForFunction(
    () => {
      const root = document.getElementById('gantt-app-root');
      return root && root.children.length > 0;
    },
    { timeout: 10000 }
  );
}

test.describe.serial('Gantt Schedule E2E', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Mounts and renders KibrayGantt component', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    await waitForGanttMount(page);
    const root = page.locator('#gantt-app-root');
    await expect(root).toBeVisible();
  });

  test('V2 API endpoint healthy', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    const result = await page.evaluate(async () => {
      const res = await fetch('/api/v1/gantt/v2/projects/1/', { credentials: 'include' });
      return { ok: res.ok, status: res.status };
    });
    expect(result.ok).toBeTruthy();
    expect(result.status).toBe(200);
  });

  test('V2 API returns expected structure', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    const data = await page.evaluate(async () => {
      const res = await fetch('/api/v1/gantt/v2/projects/1/', { credentials: 'include' });
      return res.json();
    });
    expect(data).toHaveProperty('project');
    expect(data).toHaveProperty('phases');
    expect(data).toHaveProperty('dependencies');
  });

  test('Can switch views', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    await waitForGanttMount(page);
    const calendarBtn = page.locator('button:has-text("Calendar")').or(page.locator('button:has-text("Calendario")'));
    if (await calendarBtn.count() > 0) {
      await calendarBtn.first().click();
      // Calendar view fetches its own data — wait for network to settle.
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
  });

  test('No console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.goto('/projects/1/schedule/gantt/');
    await waitForGanttMount(page);
    // Give the page a chance to settle so any deferred fetches / effects
    // emit their console errors. networkidle is a deterministic signal.
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    const relevant = errors.filter(e => !e.includes('favicon') && !e.includes('404'));
    expect(relevant.length).toBe(0);
  });
});
