import { test, expect } from '@playwright/test';

const dashboards = [
  { path: '/dashboard/admin/', label: 'Admin', modernMarker: '#kb-sidebar' },
  { path: '/dashboard/designer/', label: 'Dashboard Diseñador', modernMarker: '#kb-sidebar' },
];

test.describe('Unified dashboard shell', () => {
  for (const dash of dashboards) {
    test(`${dash.label} uses modern shell and has no horizontal overflow`, async ({ page }) => {
      await page.setViewportSize({ width: 360, height: 800 });
      await page.goto(dash.path);
      await page.waitForSelector(dash.modernMarker, { timeout: 5000 });

      // Verify modern nav markers
      const sidebar = page.locator(dash.modernMarker);
      await expect(sidebar).toBeVisible();
      await expect(page.locator('[data-layout-root]')).toBeVisible();

      // Check no horizontal overflow at common small width
  await page.waitForTimeout(300);
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth);

      // Toggle mobile menu to ensure overlay works and closes with ESC
      const toggle = page.locator('#mobile-menu-toggle');
      await toggle.click();
      await expect(sidebar).toHaveClass(/translate-x-0|transform-none/);
      await page.keyboard.press('Escape');
      await expect(sidebar).toHaveClass(/-translate-x-full/);
    });
  }
});
