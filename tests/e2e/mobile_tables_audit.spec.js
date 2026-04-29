// @ts-check
/**
 * Mobile-tables audit sweep.
 *
 * Goal
 * ----
 * Regression net for the new global responsive-table layer
 * (`core/static/css/responsive-tables.css` +
 *  `core/static/js/responsive-tables.js`), which auto-wraps every <table> in
 * a horizontally scrollable container so it stays usable on phones.
 *
 * For every route in ROUTES, this spec:
 *   1. Sets a phone-sized viewport (iPhone-12 width = 390px).
 *   2. Loads the page (skips 4xx/5xx).
 *   3. For every visible <table>:
 *        a. Assert the table is `kb-mobile-cards` (card layout — no overflow
 *           by design), OR
 *        b. Assert the table sits inside a horizontally scrollable ancestor
 *           (`.kb-table-scroll`, `.table-responsive`, or any element whose
 *           computed `overflow-x` is `auto`/`scroll`), AND that ancestor's
 *           clientWidth is ≤ viewport width — i.e. the table can scroll
 *           independently and does NOT push the page wider than the screen.
 *   4. Also assert the page itself does not horizontally overflow
 *      (`document.documentElement.scrollWidth ≤ innerWidth + 1`), which is
 *      the user-visible symptom of a non-responsive table.
 *
 * Failures include a diagnostic snippet pointing at the offending table so
 * the next agent knows exactly which template to fix.
 */

import { test, expect } from '@playwright/test';

const ROUTES = [
  { path: '/tasks/', name: 'Tasks list' },
  { path: '/projects/1/tasks/', name: 'Project tasks list' },
  { path: '/projects/1/rfis/', name: 'Project RFI list' },
  { path: '/projects/1/risks/', name: 'Project risks list' },
  { path: '/projects/1/damages/', name: 'Project damage reports' },
  { path: '/projects/1/inventory/', name: 'Project inventory view' },
  { path: '/invoices/', name: 'Invoices list' },
  { path: '/projects/', name: 'Projects list' },
  { path: '/clients/', name: 'Clients list' },
  { path: '/dashboard/admin/', name: 'Admin dashboard' },
  { path: '/dashboard/pm/', name: 'PM dashboard' },
  { path: '/dashboard/employee/', name: 'Employee dashboard' },
  { path: '/payroll/week/', name: 'Payroll weekly review' },
  { path: '/payroll/history/', name: 'Payroll payment history' },
  { path: '/incomes/', name: 'Income list' },
  { path: '/planning/list/', name: 'Daily plans list' },
  { path: '/inventory/low-stock/', name: 'Inventory low stock' },
  { path: '/organizations/', name: 'Organizations list' },
];

const VIEWPORT = { width: 390, height: 844 }; // iPhone 12 / 13 / 14
const SLACK_PX = 4;                            // sub-pixel + scrollbar slack

test.describe('Mobile tables audit @ 390px', () => {
  test.use({ viewport: VIEWPORT });

  for (const route of ROUTES) {
    test(`${route.name} — tables fit and scroll cleanly`, async ({ page }) => {
      const resp = await page.goto(route.path, { waitUntil: 'domcontentloaded' });
      if (!resp || resp.status() >= 400) {
        test.skip(true, `route ${route.path} returned ${resp ? resp.status() : 'no response'}`);
      }

      // Give the responsive-tables MutationObserver a tick to wrap tables.
      await page.waitForTimeout(150);

      // ---- 1. Page-level horizontal overflow check ---------------------
      const pageOverflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      }));
      expect.soft(
        pageOverflow.scrollWidth,
        `page overflows horizontally on ${route.path}: ` +
        `scrollWidth=${pageOverflow.scrollWidth} > innerWidth=${pageOverflow.innerWidth}`
      ).toBeLessThanOrEqual(pageOverflow.innerWidth + SLACK_PX);

      // ---- 2. Per-table check ------------------------------------------
      const reports = await page.evaluate((slack) => {
        function ancestorScrollX(el) {
          let node = el.parentElement;
          while (node && node !== document.body) {
            if (node.matches('.kb-table-scroll, .table-responsive')) return node;
            const cs = getComputedStyle(node);
            if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') &&
                node.clientWidth > 0) {
              return node;
            }
            node = node.parentElement;
          }
          return null;
        }

        const out = [];
        document.querySelectorAll('table').forEach((t, i) => {
          const cs = getComputedStyle(t);
          if (cs.display === 'none' || cs.visibility === 'hidden') return;
          const rect = t.getBoundingClientRect();
          if (rect.width === 0 || rect.height === 0) return;

          const isCards = t.classList.contains('kb-mobile-cards');
          const scroller = ancestorScrollX(t);
          const winW = window.innerWidth;

          out.push({
            index: i,
            id: t.id || null,
            classList: t.className,
            tag: t.outerHTML.substring(0, 160),
            isCards,
            hasScroller: !!scroller,
            scrollerClass: scroller ? scroller.className : null,
            scrollerWidth: scroller ? scroller.clientWidth : null,
            tableWidth: rect.width,
            winW,
          });
        });
        return out;
      }, SLACK_PX);

      for (const r of reports) {
        const label = `table[#${r.index}]${r.id ? '#' + r.id : ''} (${r.classList || 'no-class'})`;

        if (r.isCards) {
          // Card layout: should not overflow viewport width itself.
          expect.soft(
            r.tableWidth,
            `${label} uses .kb-mobile-cards but still wider than viewport on ${route.path}`
          ).toBeLessThanOrEqual(r.winW + SLACK_PX);
          continue;
        }

        // Otherwise it MUST be inside a horizontal scroller.
        expect(
          r.hasScroller,
          `${label} on ${route.path} has no horizontally scrollable ancestor.\n` +
          `  Snippet: ${r.tag}\n` +
          `  Fix: add class="kb-mobile-cards" to the <table> for card layout, ` +
          `or wrap it with <div class="table-responsive">. ` +
          `Note: the global responsive-tables.js auto-wraps tables; if this ` +
          `failed, check the page is loading base_modern.html.`
        ).toBe(true);

        // The scroller itself must not widen the page.
        expect.soft(
          r.scrollerWidth,
          `${label} scroller (${r.scrollerClass}) on ${route.path} is wider than the viewport ` +
          `(${r.scrollerWidth} > ${r.winW}) — fix the parent layout.`
        ).toBeLessThanOrEqual(r.winW + SLACK_PX);
      }
    });
  }
});
