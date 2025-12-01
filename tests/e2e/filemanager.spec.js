import { test, expect } from '@playwright/test';

test.describe('File Manager', () => {
  test('navigate to file manager', async ({ page }) => {
    // Listen to ALL navigation events
    page.on('framenavigated', frame => {
      if (frame === page.mainFrame()) {
        console.log('NAVIGATED TO:', frame.url());
      }
    });
    
    // Listen to console messages and errors
    page.on('console', msg => console.log(`BROWSER ${msg.type()}: ${msg.text()}`));
    page.on('pageerror', err => console.log(`PAGE ERROR: ${err.message}`));
    
    await page.goto('/files', { waitUntil: 'networkidle' });
    
    // Check localStorage
    const authToken = await page.evaluate(() => localStorage.getItem('authToken'));
    console.log('Auth token in localStorage:', authToken);
    
    // Wait for React to render
    await page.waitForTimeout(3000);
    
    const currentURL = page.url();
    console.log('Final URL:', currentURL);
    
    // Check if File Manager h1 exists
    const h1Count = await page.locator('h1').count();
    console.log('H1 tags found:', h1Count);
    
    if (h1Count > 0) {
      const h1Texts = await page.locator('h1').allTextContents();
      console.log('H1 texts:', h1Texts);
    }
    
    await expect(page.locator('text=File Manager')).toBeVisible({ timeout: 10000 });
  });
});
