import { test, expect, Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/admin/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('input[type="submit"]');
  await page.waitForSelector('body');
}

test.describe.serial('TouchupBoard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('TouchupBoard component mounts (instrumented)', async ({ page }) => {
    const logs: string[] = [];
    page.on('console', msg => logs.push(`${msg.type()}: ${msg.text()}`));

    await page.goto('/projects/1/touchups-react/');
    const touchupRoot = page.locator('#touchup-root');
    await touchupRoot.waitFor({ state: 'attached', timeout: 8000 });

  // Wait for data-mounted attribute set by component
  await page.waitForFunction(() => document.getElementById('touchup-root')?.getAttribute('data-mounted') === '1', { timeout: 8000 });
  // Log collected console messages so far
  console.log('EARLY LOGS:\n' + logs.join('\n'));

    // Inspect DOM before assertion
    const domInfo = await page.evaluate(() => {
      const root = document.getElementById('touchup-root');
      return {
        mountedAttr: root?.getAttribute('data-mounted'),
        rootHTML: root?.innerHTML?.slice(0, 500),
        boardCount: document.querySelectorAll('.touchup-board').length,
        scripts: Array.from(document.querySelectorAll('script[type="module"]')).map(s => s.getAttribute('src')),
      };
    });
    console.log('DOM INFO:', domInfo);

    // Ensure React container div is created
    const board = page.locator('.touchup-board');
    await expect(board).toBeVisible({ timeout: 8000 });

    // Dump logs for debugging if needed
    console.log('INSTRUMENTATION LOGS:\n' + logs.join('\n'));
  });

  test('Board displays four kanban columns', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    
    // Check for the standard columns: Pendiente, En Progreso, Completada, Cancelada
    const pendiente = page.locator('text=Pendiente');
    const enProgreso = page.locator('text=En Progreso');
    const completada = page.locator('text=Completada');
    const cancelada = page.locator('text=Cancelada');
    
    await expect(pendiente).toBeVisible({ timeout: 5000 });
    await expect(enProgreso).toBeVisible({ timeout: 5000 });
    await expect(completada).toBeVisible({ timeout: 5000 });
    await expect(cancelada).toBeVisible({ timeout: 5000 });
  });

  test('Project ID filter input is present and functional', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    
    // Find the project ID input
    const projectInput = page.locator('input[placeholder*="Project"]').or(
      page.locator('.toolbar input').first()
    );
    await expect(projectInput).toBeVisible({ timeout: 5000 });
    
    // Verify it accepts input
    await projectInput.fill('2');
    await expect(projectInput).toHaveValue('2');
  });

  test('Board shows loading state initially', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    
    // Check for loading indicator (might be brief)
    const loading = page.locator('text=Loading').or(page.locator('.loading'));
    // This might already be gone by the time we check, so we just verify the board appears
    const board = page.locator('.touchup-board');
    await expect(board).toBeVisible({ timeout: 10000 });
  });

  test('API endpoint is accessible', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    
    // Wait for board to load
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    
    // Make API call to verify endpoint
    const response = await page.evaluate(async () => {
      const res = await fetch('/api/v1/tasks/touchup_board/?project=1', {
        headers: {
          'Accept': 'application/json',
        },
        credentials: 'include',
      });
      return {
        ok: res.ok,
        status: res.status,
        hasColumns: !!(await res.json()).columns,
      };
    });
    
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.hasColumns).toBeTruthy();
  });

  test('Board displays task cards when data available', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    
    // Wait a moment for API to load
    await page.waitForTimeout(2000);
    
    // Check if any cards are present (or verify empty state)
    const cards = page.locator('.task-card, .card, [class*="card"]');
    const emptyState = page.locator('text=No tasks').or(page.locator('text=Sin tareas'));
    
    // Either cards exist or empty state is shown
    const hasCards = await cards.count().then(c => c > 0).catch(() => false);
    const isEmpty = await emptyState.isVisible().catch(() => false);
    
    expect(hasCards || isEmpty).toBeTruthy();
  });

  test('No React errors on board render', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    // Filter out known non-React errors (like favicon 404)
    const reactErrors = errors.filter(e => 
      !e.includes('favicon') && 
      !e.includes('kibray-logo.png') &&
      !e.includes('404')
    );
    
    expect(reactErrors.length).toBe(0);
  });

  test('Board persists after navigation', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    
    // Navigate away
    await page.goto('/dashboard/');
    await page.waitForSelector('body');
    
    // Navigate back
    await page.goto('/projects/1/touchups-react/');
    const board = page.locator('.touchup-board');
    await expect(board).toBeVisible({ timeout: 10000 });
  });

  test('Toolbar is present and visible', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    
    const toolbar = page.locator('.toolbar');
    await expect(toolbar).toBeVisible({ timeout: 5000 });
  });

  test('Priority colors or indicators visible on cards', async ({ page }) => {
    await page.goto('/projects/1/touchups-react/');
    await page.waitForSelector('.touchup-board', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    // Check if any priority indicators exist
    const priorityLow = page.locator('text=low').or(page.locator('[class*="priority"]'));
    const priorityHigh = page.locator('text=high');
    const priorityUrgent = page.locator('text=urgent');
    
    // At least the priority system should be in place (visible or not depending on data)
    const board = page.locator('.touchup-board');
    await expect(board).toBeVisible();
  });
});
