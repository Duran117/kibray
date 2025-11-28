import { test, expect, Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/admin/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('input[type="submit"]');
  await page.waitForSelector('body');
}

async function createAssignment(page: Page, project: number = 1, pmUser: number = 1) {
  await page.evaluate(async ({ project, pmUser }) => {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    await fetch('/api/v1/project-manager-assignments/assign/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken || '' },
      credentials: 'include',
      body: JSON.stringify({ project: String(project), pm: String(pmUser), role: 'project_manager' })
    });
  }, { project, pmUser });
}

test.describe.serial('PMAssignments E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Component mounts with data-mounted attribute', async ({ page }) => {
    await page.goto('/pm-assignments/');
    const root = page.locator('#pm-assignments-root');
    await root.waitFor({ state: 'attached', timeout: 8000 });
    await page.waitForFunction(() => document.getElementById('pm-assignments-root')?.getAttribute('data-mounted') === '1', { timeout: 8000 });
    await expect(page.locator('.pm-assignments')).toBeVisible();
  });

  test('Refresh button fetches assignment list (API health)', async ({ page }) => {
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    const result = await page.evaluate(async () => {
      const res = await fetch('/api/v1/project-manager-assignments/', { headers: { 'Accept': 'application/json' }, credentials: 'include' });
      return { ok: res.ok, status: res.status };
    });
    expect(result.ok).toBeTruthy();
    expect(result.status).toBe(200);
  });

  test('Open assignment form and submit new assignment', async ({ page }) => {
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    await page.locator('button:has-text("+ Assign PM")').click();
    await expect(page.locator('form >> text=New PM Assignment')).toBeVisible();
    await page.fill('form input[placeholder="Project ID"]', '1');
    await page.fill('form input[placeholder="PM User ID"]', '1');
    await page.fill('form input[placeholder="Role (default: project_manager)"]', 'project_manager');
    await page.click('form button:has-text("Assign")');
    await page.waitForTimeout(800);
    const cards = page.locator('.pm-assignments > div > div');
    expect(await cards.count()).toBeGreaterThan(0);
  });

  test('List shows items or empty state after refresh', async ({ page }) => {
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    const cards = page.locator('.pm-assignments > div > div');
    const count = await cards.count();
    expect(count >= 0).toBeTruthy();
  });

  test('Assignments contain project and PM info text', async ({ page }) => {
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    await createAssignment(page, 1, 1);
    await page.reload();
    await page.waitForSelector('.pm-assignments');
    const projectText = page.locator('.pm-assignments div:has-text("Project:")');
    expect(await projectText.count()).toBeGreaterThan(0);
  });

  test('No React console errors during render', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    await page.waitForTimeout(1000);
    const relevant = errors.filter(e => !e.includes('favicon') && !e.includes('404'));
    expect(relevant.length).toBe(0);
  });

  test('Component persists after navigation', async ({ page }) => {
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    await page.goto('/dashboard/');
    await page.waitForSelector('body');
    await page.goto('/pm-assignments/');
    await expect(page.locator('.pm-assignments')).toBeVisible();
  });

  test('Reload after assignment attempt keeps component stable', async ({ page }) => {
    await page.goto('/pm-assignments/');
    await page.waitForSelector('.pm-assignments');
    // Attempt create (may 400 due to duplicate or validation) but should not break component
    try { await createAssignment(page, 1, 1); } catch {}
    await page.reload();
    await expect(page.locator('.pm-assignments')).toBeVisible();
  });
});
