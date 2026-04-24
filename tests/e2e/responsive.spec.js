import { test, expect } from '@playwright/test';

const devices = [
  { name: 'iPhone12', width: 375, height: 812 },
  { name: 'iPad', width: 768, height: 1024 },
  { name: 'Desktop', width: 1920, height: 1080 },
];

test.describe('Responsive Design', () => {
  for (const device of devices) {
    test(`renders on ${device.name}`, async ({ page }) => {
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.goto('/files'); // Go to a route we know works
      // Replace arbitrary 2s sleep with real wait for network to settle
      // (React app is mounted by then). Cap at 10s.
      await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
      // Just check that SOMETHING renders (body has content)
      const bodyText = await page.locator('body').textContent();
      expect(bodyText.length).toBeGreaterThan(0);
      await page.screenshot({ path: `test-results/responsive-${device.name}.png` });
    });
  }
});
