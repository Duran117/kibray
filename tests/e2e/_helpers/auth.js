// @ts-check
/**
 * Shared E2E auth helpers.
 *
 * Centralises credential management. All specs should import from here
 * rather than hardcoding usernames/passwords. Defaults match
 * tests/e2e/auth.setup.js so storageState-based runs work out of the box.
 *
 * Override per-environment with:
 *   E2E_ADMIN_USER=...  E2E_ADMIN_PASS=...
 */

export const ADMIN_USER = process.env.E2E_ADMIN_USER || 'admin_playwright';
export const ADMIN_PASS = process.env.E2E_ADMIN_PASS || 'admin123';

/**
 * Perform a UI login (used by specs that don't rely on storageState).
 * @param {import('@playwright/test').Page} page
 */
export async function loginAsAdmin(page) {
  await page.goto('/login/?next=/');
  await page.fill('input[name="username"]', ADMIN_USER);
  await page.fill('input[name="password"]', ADMIN_PASS);
  await Promise.all([
    page.waitForLoadState('networkidle'),
    page.click('button[type="submit"], input[type="submit"]'),
  ]);
}
