// @ts-check
/**
 * UI Audit sweep — detects modals/overlays trapped under the sidebar.
 *
 * Background
 * ----------
 * The app's `base_modern.html` declares `#main-content > div { z-index: 1 }`
 * which creates a stacking context. Any descendant `.modal` (Bootstrap) or
 * fixed-position overlay (e.g. payroll hour-entry editor) becomes trapped
 * BELOW the sidebar (`z-40`), so dropdowns are unclickable and parts of the
 * panel render under the dark sidebar.
 *
 * The fix in `base_modern.html` re-parents `.modal` to <body> on
 * `show.bs.modal`, and known custom overlays to <body> on DOMContentLoaded.
 *
 * This spec is a regression net: it visits a curated list of routes, opens
 * every Bootstrap modal trigger it finds, and asserts that:
 *   1. The modal becomes visible.
 *   2. Its center pixel is owned by the modal (or a descendant), not by the
 *      sidebar / header / other overlay → guarantees clicks land on it.
 *   3. The first focusable input/select inside is also topmost at its center
 *      → guarantees the user can actually interact with form controls.
 *
 * It also checks every page-level fixed overlay (entry-modal-overlay,
 * mobile-drawer-overlay) for the same property when set to `.active`.
 *
 * The sweep is intentionally pragmatic — it skips routes that 404/500 instead
 * of failing, so missing fixtures don't break the suite. Any concrete bug
 * found is a hard failure with a screenshot.
 */

import { test, expect } from '@playwright/test';

// --- Routes worth auditing for modals/overlays ----------------------------
// Keep this list short and stable; expand only when a route is known to host
// a modal or a custom overlay.
const ROUTES = [
  { path: '/invoices/', name: 'Invoices list (createInvoiceModal)' },
  { path: '/dashboard/admin/', name: 'Admin dashboard' },
  { path: '/dashboard/pm/', name: 'PM dashboard' },
  { path: '/projects/', name: 'Projects list' },
  { path: '/pm-calendar/', name: 'PM calendar (blockDayModal)' },
  { path: '/payroll/week/', name: 'Payroll weekly review (entry-modal-overlay)' },
];

/**
 * Returns the `<body>`-relative bounding box of an element, or null if hidden.
 * @param {import('@playwright/test').Locator} loc
 */
async function bbox(loc) {
  try { return await loc.boundingBox(); } catch { return null; }
}

/**
 * Asserts that `topLoc` owns several sample pixels (center + corners + a
 * point near the left edge that would naturally be covered by the sidebar).
 * For each sample point, the result of `document.elementFromPoint(x, y)` must
 * be the element itself or one of its descendants. This proves the element
 * is not visually covered — including by the fixed sidebar at z=40, which is
 * the most common offender for modals trapped in `#main-content` stacking
 * context.
 *
 * @param {import('@playwright/test').Page} page
 * @param {import('@playwright/test').Locator} topLoc
 * @param {string} label
 */
async function expectTopmostAtSamplePoints(page, topLoc, label) {
  const box = await bbox(topLoc);
  expect(box, `${label}: element has no bounding box`).not.toBeNull();
  if (!box) return;
  const handle = await topLoc.elementHandle();
  expect(handle, `${label}: no element handle`).not.toBeNull();
  if (!handle) return;

  // Sample several points: center, near each corner (10% inset).
  const samples = [
    { name: 'center', x: box.x + box.width / 2, y: box.y + box.height / 2 },
    { name: 'top-left', x: box.x + Math.max(8, box.width * 0.1), y: box.y + Math.max(8, box.height * 0.1) },
    { name: 'top-right', x: box.x + box.width - Math.max(8, box.width * 0.1), y: box.y + Math.max(8, box.height * 0.1) },
    { name: 'bottom-left', x: box.x + Math.max(8, box.width * 0.1), y: box.y + box.height - Math.max(8, box.height * 0.1) },
    { name: 'bottom-right', x: box.x + box.width - Math.max(8, box.width * 0.1), y: box.y + box.height - Math.max(8, box.height * 0.1) },
  ];

  for (const s of samples) {
    const cx = Math.round(s.x);
    const cy = Math.round(s.y);
    // Skip points outside the viewport.
    const viewport = page.viewportSize();
    if (viewport && (cx < 0 || cy < 0 || cx >= viewport.width || cy >= viewport.height)) continue;
    const result = await page.evaluate(
      ([x, y, target]) => {
        const hit = document.elementFromPoint(x, y);
        if (!hit) return { owned: false, tag: null, id: null, cls: null };
        const owned = hit === target || target.contains(hit);
        return {
          owned,
          tag: hit.tagName,
          id: hit.id,
          cls: hit.className && hit.className.toString ? hit.className.toString().slice(0, 120) : '',
        };
      },
      [cx, cy, handle]
    );
    expect(
      result.owned,
      `${label}: pixel (${cx},${cy}) [${s.name}] is owned by ` +
        `<${result.tag} id="${result.id}" class="${result.cls}"> instead of the expected element. ` +
        `This means the sidebar (z-40) or another overlay is covering it — ` +
        `usually a stacking-context trap from #main-content > div { z-index: 1 }.`
    ).toBe(true);
  }
}

/** Backwards-compat alias */
const expectTopmostAtCenter = expectTopmostAtSamplePoints;

test.describe('UI audit — modals & overlays are not trapped under the sidebar', () => {
  test.describe.configure({ mode: 'serial' });

  for (const route of ROUTES) {
    test(`route ${route.path} — ${route.name}`, async ({ page }, testInfo) => {
      const resp = await page.goto(route.path, { waitUntil: 'domcontentloaded' });
      // Skip routes the test user can't reach (404/403/500). The audit only
      // cares about pages that actually render.
      if (!resp || resp.status() >= 400) {
        test.skip(true, `route ${route.path} returned ${resp ? resp.status() : 'no response'}`);
        return;
      }
      await page.waitForLoadState('networkidle').catch(() => {});

      // ── 1. Bootstrap modals ───────────────────────────────────
      const triggers = page.locator('[data-bs-toggle="modal"][data-bs-target]');
      const triggerCount = await triggers.count();
      for (let i = 0; i < triggerCount; i++) {
        const trig = triggers.nth(i);
        if (!(await trig.isVisible().catch(() => false))) continue;
        const target = await trig.getAttribute('data-bs-target');
        if (!target || !target.startsWith('#')) continue;
        const modal = page.locator(target);
        if ((await modal.count()) === 0) continue;

        await trig.scrollIntoViewIfNeeded().catch(() => {});
        await trig.click({ trial: false }).catch(() => {});
        // Bootstrap adds .show on the modal once visible.
        await expect(modal, `modal ${target} did not become visible`).toBeVisible({ timeout: 2000 });
        // Wait for the show transition to settle.
        await page.waitForTimeout(350);

        // The modal-content is the actual interactive panel (modal-dialog
        // uses pointer-events: none by Bootstrap design so empty regions
        // pass clicks through to the backdrop for outside-dismiss).
        const content = modal.locator('.modal-content').first();
        await expectTopmostAtSamplePoints(page, content, `${route.path} ${target} content`);

        // First focusable input/select/textarea inside the modal must also be on top.
        const firstField = modal.locator('select, input:not([type="hidden"]), textarea').first();
        if (await firstField.count() > 0 && await firstField.isVisible().catch(() => false)) {
          await expectTopmostAtCenter(
            page,
            firstField,
            `${route.path} ${target} first form control`
          );
        }

        // Close before opening the next one.
        const closeBtn = modal.locator('[data-bs-dismiss="modal"]').first();
        if (await closeBtn.count() > 0) {
          await closeBtn.click().catch(() => {});
          await page.waitForTimeout(250);
        } else {
          await page.keyboard.press('Escape');
          await page.waitForTimeout(250);
        }
      }

      // ── 2. Known custom overlays ─────────────────────────────
      // For each known overlay class, force-add `.active` and check it's on top
      // — including at x=20 (sidebar territory) which is where the trapped
      // stacking-context bug actually manifests visually for the user.
      const overlaySelectors = ['.entry-modal-overlay', '.mobile-drawer-overlay'];
      for (const sel of overlaySelectors) {
        const overlay = page.locator(sel).first();
        if ((await overlay.count()) === 0) continue;
        // Make it visible without going through the page-specific opener.
        await page.evaluate((s) => {
          const el = document.querySelector(s);
          if (el) {
            el.classList.add('active');
            el.style.display = 'flex';
            el.style.opacity = '1';
            el.style.pointerEvents = 'auto';
          }
        }, sel);
        await page.waitForTimeout(150);
        if (!(await overlay.isVisible().catch(() => false))) continue;

        // Sample-point check: center + corners.
        await expectTopmostAtSamplePoints(page, overlay, `${route.path} overlay ${sel}`);

        // Hard sidebar-territory check: at x=20, y=300 the overlay must own the pixel
        // (not the sidebar). This is the EXACT failure mode the user reported.
        const handle = await overlay.elementHandle();
        if (handle) {
          const owned = await page.evaluate(
            ([x, y, target]) => {
              const hit = document.elementFromPoint(x, y);
              return hit && (hit === target || target.contains(hit));
            },
            [20, 300, handle]
          );
          expect(
            owned,
            `${route.path} overlay ${sel}: pixel (20,300) is covered by the sidebar — ` +
              `the overlay is trapped inside #main-content stacking context. ` +
              `Reparent to <body> on show.`
          ).toBe(true);
        }

        // Cleanup so subsequent assertions on the page aren't affected.
        await page.evaluate((s) => {
          const el = document.querySelector(s);
          if (el) {
            el.classList.remove('active');
            el.style.display = '';
            el.style.opacity = '';
            el.style.pointerEvents = '';
          }
        }, sel);
      }
    });
  }
});
