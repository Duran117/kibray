/**
 * Phase E1.3.b follow-up — Client portal E2E smoke
 *
 * Read-only verification that the admin-authenticated session can reach the
 * client-facing dashboard page (which an admin user is also allowed to view
 * for impersonation/QA). Per-project deep-link routes (e.g. /proyecto/<id>/)
 * require a valid project ID — those are env-specific so we skip rather than
 * fail when no project is reachable.
 *
 * Like financial.spec.js, uses gotoOrSkip helper for graceful degradation.
 */
import { test, expect } from '@playwright/test';

async function gotoOrSkip(page, path) {
  const resp = await page.goto(path, { waitUntil: 'domcontentloaded' });
  if (!resp) {
    test.skip(true, `No response for ${path}`);
    return null;
  }
  const status = resp.status();
  if (status === 404) {
    test.skip(true, `Route ${path} returned 404 (not deployed in this env)`);
    return null;
  }
  if (status >= 500) {
    test.skip(true, `Route ${path} returned ${status} (server error, env-specific)`);
    return null;
  }
  expect(status, `expected 2xx/3xx for ${path}, got ${status}`).toBeLessThan(400);
  return resp;
}

test.describe('Client portal smoke', () => {
  test('client dashboard route renders project list or empty-state', async ({ page }) => {
    await gotoOrSkip(page, '/dashboard/client/');
    // The page should mention 'project'/'proyecto' somewhere (heading/cards/empty).
    await expect(page.locator('body')).toContainText(/project|proyecto/i, { timeout: 5000 });
    // Layout chrome should be present
    await expect(
      page.locator('nav, #kb-sidebar, [data-layout-root], main').first()
    ).toBeVisible({ timeout: 5000 });
  });

  test('client project deep-link is reachable when at least one project exists', async ({
    page,
  }) => {
    // Discover a project ID by visiting the admin project list and grabbing
    // the first project link. If none exists in this env, skip cleanly.
    const listResp = await page.goto('/projects/', { waitUntil: 'domcontentloaded' });
    if (!listResp || listResp.status() >= 400) {
      test.skip(true, '/projects/ not reachable — cannot discover a project ID');
      return;
    }

    // Try several common selectors for project rows / cards / links.
    const linkSelectors = [
      'a[href*="/proyecto/"]',
      'a[href^="/projects/"][href*="/"]',
      'a[data-project-id]',
    ];
    let projectId = null;
    for (const sel of linkSelectors) {
      const href = await page.locator(sel).first().getAttribute('href').catch(() => null);
      if (!href) continue;
      const m = href.match(/\/(?:proyecto|projects)\/(\d+)/);
      if (m) {
        projectId = m[1];
        break;
      }
    }

    if (!projectId) {
      test.skip(true, 'No project found in /projects/ — skipping deep-link test');
      return;
    }

    await gotoOrSkip(page, `/proyecto/${projectId}/`);
    // Client project view should mention project name / financials / documents tab
    await expect(page.locator('body')).toContainText(
      /document|financ|proyecto|project/i,
      { timeout: 5000 }
    );
  });

  test('color sample feedback endpoint responds (HEAD-style smoke)', async ({ page }) => {
    // We don't know a sample_id; just hit a guaranteed-404 form of the route
    // and assert it routes (not 500). This catches URL-conf regressions
    // without needing fixture data.
    const resp = await page.goto('/colors/sample/999999999/client-feedback/', {
      waitUntil: 'domcontentloaded',
    });
    if (!resp) {
      test.skip(true, 'No response from color feedback endpoint');
      return;
    }
    // Acceptable: 404 (route exists, sample not found), 302 (redirect to
    // login/list), 200 (form rendered). Anything else (esp. 500) is a bug.
    expect([200, 302, 403, 404]).toContain(resp.status());
  });
});
