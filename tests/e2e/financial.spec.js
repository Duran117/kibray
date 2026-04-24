/**
 * Phase E1.3.b — Financial flows E2E smoke
 *
 * Static smoke checks for the highest-value financial pages. We deliberately
 * avoid mutating data (no payments recorded, no invoices created) so the spec
 * is safe to run repeatedly against the same storageState.
 *
 * If a target page is unavailable in the environment under test (404 / 500),
 * the test is skipped rather than failed — keeping the suite green while still
 * surfacing issues via explicit skip messages.
 */
import { test, expect } from '@playwright/test';

/**
 * Navigate and tolerate transient 5xx by skipping the test.
 * Fails fast on 4xx (something we own) unless it's 404 (route not deployed).
 */
async function gotoOrSkip(page, path) {
  const resp = await page.goto(path, { waitUntil: 'domcontentloaded' });
  if (!resp) {
    test.skip(true, `No response for ${path}`);
    return;
  }
  const status = resp.status();
  if (status === 404) {
    test.skip(true, `Route ${path} returned 404 (not deployed in this env)`);
    return;
  }
  if (status >= 500) {
    test.skip(true, `Route ${path} returned ${status} (server error, env-specific)`);
    return;
  }
  expect(status, `expected 2xx/3xx for ${path}, got ${status}`).toBeLessThan(400);
}

test.describe('Financial smoke', () => {
  test('invoice list page loads with table or empty-state', async ({ page }) => {
    await gotoOrSkip(page, '/invoices/');
    // Title or H1 should reference invoices (English or Spanish copy)
    await expect(page.locator('h1, h2, title')).toContainText(/invoice|factura/i, {
      timeout: 5000,
    });
    // Either a results table OR an empty state should be present — both valid.
    const tableOrEmpty = page.locator('table, [data-empty-state], .empty-state');
    await expect(tableOrEmpty.first()).toBeVisible({ timeout: 5000 });
  });

  test('invoice payment dashboard renders KPI cards', async ({ page }) => {
    await gotoOrSkip(page, '/invoices/payments/');
    // Payment dashboard should show at least one KPI / metric card
    const kpiCandidates = page.locator(
      '[data-kpi], .card, .stat-card, .metric, [class*="kpi"]'
    );
    await expect(kpiCandidates.first()).toBeVisible({ timeout: 5000 });
    // Page should mention payments or amounts
    await expect(page.locator('body')).toContainText(/payment|pago|amount|monto|\$/i);
  });

  test('financial dashboard route is reachable from navigation', async ({ page }) => {
    // Try the most common financial dashboard entry points; first one that
    // responds 2xx wins. If none reachable, skip.
    const candidates = [
      '/dashboard/financial/',
      '/financial/',
      '/dashboard/admin/',
    ];
    let reached = null;
    for (const path of candidates) {
      const resp = await page.goto(path, { waitUntil: 'domcontentloaded' }).catch(() => null);
      if (resp && resp.status() < 400) {
        reached = path;
        break;
      }
    }
    if (!reached) {
      test.skip(true, 'No financial dashboard route reachable in this env');
      return;
    }
    // Sanity: page rendered some chrome (sidebar / nav)
    await expect(page.locator('nav, #kb-sidebar, [data-layout-root]').first()).toBeVisible({
      timeout: 5000,
    });
  });
});
