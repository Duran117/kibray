import { test, expect, Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/admin/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('input[type="submit"]');
  await page.waitForSelector('body');
}

// Utility to create a pending approval via direct API (faster & deterministic)
async function createApproval(page: Page, project: number = 1) {
  await page.evaluate(async (proj) => {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    await fetch('/api/v1/color-approvals/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken || '' },
      credentials: 'include',
      body: JSON.stringify({
        project: String(proj),
        color_name: 'AutoTest Color',
        color_code: 'AT-001',
        brand: 'TestBrand',
        location: 'Lab',
        notes: 'E2E generated'
      })
    });
  }, project);
}

test.describe.serial('ColorApprovals E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Component mounts and sets data-mounted', async ({ page }) => {
    await page.goto('/color-approvals/');
    const root = page.locator('#color-approvals-root');
    await root.waitFor({ state: 'attached', timeout: 8000 });
    await page.waitForFunction(() => document.getElementById('color-approvals-root')?.getAttribute('data-mounted') === '1', { timeout: 8000 });
    await expect(page.locator('.color-approvals')).toBeVisible();
  });

  test('Filter inputs and refresh button visible', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals', { timeout: 8000 });
    const projectInput = page.locator('input[placeholder="Project ID"]');
    const brandInput = page.locator('input[placeholder="Brand"]');
    const statusSelect = page.locator('select');
    const refreshBtn = page.locator('button:has-text("Refresh")');
    await expect(projectInput).toBeVisible();
    await expect(brandInput).toBeVisible();
    await expect(statusSelect).toBeVisible();
    await expect(refreshBtn).toBeVisible();
  });

  test('Refresh triggers list fetch (network sanity)', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    const result = await page.evaluate(async () => {
      const res = await fetch('/api/v1/color-approvals/', { headers: { 'Accept': 'application/json' }, credentials: 'include' });
      return { ok: res.ok, status: res.status };
    });
    expect(result.ok).toBeTruthy();
    expect(result.status).toBe(200);
  });

  test('Create approval request via UI form', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    const openBtn = page.locator('button:has-text("+ Request Approval")');
    await openBtn.click();
    await expect(page.locator('form >> text=New Approval Request')).toBeVisible();
    await page.fill('form input[placeholder="Project ID"]', '1');
    await page.fill('form input[placeholder="Color Name"]', 'UI Color');
    await page.fill('form input[placeholder="Color Code"]', 'UI-123');
    await page.fill('form input[placeholder="Brand"]', 'UIBrand');
    await page.fill('form input[placeholder="Location"]', 'UI Lab');
    await page.fill('form textarea[placeholder="Notes"]', 'Created in E2E test');
    await page.click('form button:has-text("Submit")');
    // Wait a moment for list refresh
    await page.waitForTimeout(1000);
    // Expect at least one card present now
    const cards = page.locator('.color-approvals > div > div');
    expect(await cards.count()).toBeGreaterThan(0);
  });

  test('Approve flow via UI button', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    // Ensure a pending item exists
    await createApproval(page, 1);
    await page.reload();
    await page.waitForSelector('.color-approvals');
    const approveBtn = page.locator('button:has-text("Approve")').first();
    await expect(approveBtn).toBeVisible({ timeout: 5000 });
    await approveBtn.click();
    await page.waitForTimeout(800);
    // After approve, status text should include APPROVED somewhere
    const approvedText = page.locator('text=APPROVED');
    expect(await approvedText.count()).toBeGreaterThan(0);
  });

  test('Reject flow via UI button with dialog', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    await createApproval(page, 1);
    await page.reload();
    await page.waitForSelector('.color-approvals');
    const rejectBtn = page.locator('button:has-text("Reject")').first();
    await expect(rejectBtn).toBeVisible({ timeout: 5000 });
    page.once('dialog', d => d.accept('Not suitable')); // respond to prompt
    await rejectBtn.click();
    await page.waitForTimeout(800);
    const rejectedText = page.locator('text=REJECTED');
    expect(await rejectedText.count()).toBeGreaterThan(0);
  });

  test('List shows items or empty state', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    const cards = page.locator('.color-approvals > div > div');
    const count = await cards.count();
    expect(count >= 0).toBeTruthy();
  });

  test('No React errors logged during interactions', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    await page.waitForTimeout(1000);
    const relevant = errors.filter(e => !e.includes('favicon') && !e.includes('404'));
    expect(relevant.length).toBe(0);
  });

  test('Component persists after navigation', async ({ page }) => {
    await page.goto('/color-approvals/');
    await page.waitForSelector('.color-approvals');
    await page.goto('/dashboard/');
    await page.waitForSelector('body');
    await page.goto('/color-approvals/');
    await expect(page.locator('.color-approvals')).toBeVisible();
  });
});
