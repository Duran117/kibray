import { test, expect, Page } from '@playwright/test';

const ADMIN_USER = 'admin';
const ADMIN_PASS = 'Kibray2025!Admin';

test.describe('Strategic Planner E2E', () => {
  
  // Helper to log in
  async function login(page: Page) {
    await page.goto('/login/');
    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.waitFor({ state: 'visible' });
    await submitBtn.click({ force: true });
    // Wait for redirect to dashboard or home
    await expect(page).toHaveURL(/\/dashboard/);
  }

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Test 1 – Can access Strategic Planner dashboard', async ({ page }) => {
    await page.goto('/planner/strategic/');
    await expect(page).toHaveTitle(/Strategic Planner/);
    await expect(page.getByRole('heading', { name: 'Strategic Planner' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Planning Session' })).toBeVisible();
  });

  test('Test 2 – Can create a new planning session', async ({ page }) => {
    await page.goto('/planner/strategic/');
    await page.getByRole('button', { name: 'New Planning Session' }).click();
    
    // Wait for modal
    await expect(page.locator('#createSessionModal')).toBeVisible();
    
    // Select project (assuming at least one exists, select the first option that isn't placeholder)
    const projectSelect = page.locator('select[name="project"]');
    await projectSelect.click();
    // We need to wait for options to populate via fetch
    await page.waitForTimeout(1000); 
    
    // Select the second option (index 1) as index 0 is usually "Select Project..."
    await projectSelect.selectOption({ index: 1 });
    
    // Fill dates
    // Use a date in the future
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    const nextWeekEnd = new Date(nextWeek);
    nextWeekEnd.setDate(nextWeek.getDate() + 2);
    
    const startDate = nextWeek.toISOString().split('T')[0];
    const endDate = nextWeekEnd.toISOString().split('T')[0];
    
    await page.fill('input[name="start_date"]', startDate);
    await page.fill('input[name="end_date"]', endDate);
    
    await page.fill('textarea[name="notes"]', 'E2E Test Session');
    
    // Click Create
    await page.click('#saveSessionBtn');
    
    // Assert modal closes and page reloads (or new item appears)
    // Since the code does window.location.reload(), we wait for load
    await page.waitForLoadState('networkidle');
    
    // Check if the session appears in the list
    // await expect(page.locator('table')).toContainText('E2E Test Session'); // Notes aren't shown in table
    // Check for the date range or status
    await expect(page.locator('table')).toContainText('Draft');
  });

  test('Test 3 – Can open session and see Visual Board', async ({ page }) => {
    await page.goto('/planner/strategic/');
    
    // Click the first "Edit" button or the project name link
    // We'll target the first row's edit button
    const firstEditBtn = page.locator('table tbody tr').first().locator('a', { hasText: 'Edit' });
    await firstEditBtn.click();
    
    // Assert URL
    await expect(page).toHaveURL(/\/planner\/strategic\/\d+\//);
    
    // Assert Board elements
    await expect(page.locator('.overflow-x-auto')).toBeVisible(); // The board container
    // Check for day columns
    await expect(page.locator('.w-80').first()).toBeVisible(); 
  });

  test('Test 4 – Can add Items and Tasks', async ({ page }) => {
    // Navigate to the latest session
    await page.goto('/planner/strategic/');
    await page.locator('table tbody tr').first().locator('a', { hasText: 'Edit' }).click();
    
    // Add Item
    // Find the first "Add Item" button
    const addItemBtn = page.locator('button', { hasText: 'Add Item' }).first();
    await addItemBtn.click();
    
    await expect(page.locator('#addItemModal')).toBeVisible();
    await page.fill('#addItemForm input[name="title"]', 'E2E Test Item');
    await page.fill('#addItemForm input[name="estimated_hours"]', '2');
    
    // Click the submit button inside the modal
    await page.locator('#addItemModal button', { hasText: 'Add Item' }).click();
    
    await page.waitForLoadState('networkidle');
    
    // Assert Item is visible
    const itemCard = page.locator('div[data-item-id]').filter({ hasText: 'E2E Test Item' }).first();
    await expect(itemCard).toBeVisible();
    
    // Add Task
    // Hover over item to see "Add Task" button
    await itemCard.hover();
    const addTaskBtn = itemCard.locator('button', { hasText: 'Add Task' });
    await addTaskBtn.click();
    
    await expect(page.locator('#addTaskModal')).toBeVisible();
    await page.fill('#addTaskForm input[name="description"]', 'E2E Test Task');
    await page.locator('#addTaskModal button', { hasText: 'Add Task' }).click();
    
    await page.waitForLoadState('networkidle');
    
    // Assert Task is visible inside item
    await expect(itemCard).toContainText('E2E Test Task');
  });

  test('Test 5 – Drag & Drop Items between days', async ({ page }) => {
    // Navigate to session
    await page.goto('/planner/strategic/');
    await page.locator('table tbody tr').first().locator('a', { hasText: 'Edit' }).click();
    
    // Ensure we have at least 2 days. The create test made a 3 day session.
    const dayColumns = page.locator('.w-80');
    await expect(dayColumns).toHaveCount(3); // Assuming 3 days
    
    const day1 = dayColumns.nth(0);
    const day2 = dayColumns.nth(1);
    
    // Ensure Day 1 has an item (from previous test)
    const item = day1.locator('.group').first(); // .group is the item card class
    await expect(item).toBeVisible();
    
    // Drag to Day 2
    // We need to drag to the item container of Day 2
    const day2Container = day2.locator('.item-container');
    
    await item.dragTo(day2Container);
    
    // Wait for API call? The UI updates optimistically or via reload?
    // The code says: updateItemLocation -> fetch -> if ok nothing (no reload)
    // So the item should be in DOM under day 2
    
    await expect(day2Container.locator('div[data-item-id]').filter({ hasText: 'E2E Test Item' }).first()).toBeVisible();
    
    // Reload to verify persistence
    await page.reload();
    await expect(day2.locator('.item-container div[data-item-id]').filter({ hasText: 'E2E Test Item' }).first()).toBeVisible();
  });

  test('Test 6 – Export to Daily Plan', async ({ page }) => {
    // Setup dialog handler once for the entire test to accept all confirmations
    page.on('dialog', async dialog => {
        await dialog.accept();
    });

    // Navigate to session
    await page.goto('/planner/strategic/');
    await page.locator('table tbody tr').first().locator('a', { hasText: 'Edit' }).click();
    
    // Change status to Approved
    
    // Handle DRAFT -> IN_REVIEW
    const submitBtn = page.locator('button', { hasText: 'Submit for Review' });
    if (await submitBtn.isVisible()) {
        await submitBtn.click();
        await page.waitForLoadState('networkidle');
    }
    
    // Handle IN_REVIEW -> APPROVED
    const approveBtn = page.locator('button', { hasText: 'Approve Plan' });
    if (await approveBtn.isVisible()) {
         await approveBtn.click();
         await page.waitForLoadState('networkidle');
    }
    
    // Now "Export to Daily Plan" should be visible
    const exportBtn = page.locator('button', { hasText: 'Export to Daily Plan' });
    await expect(exportBtn).toBeVisible();
    
    await exportBtn.click();
    
    // Wait for success alert or reload
    // The code does: alert('Export successful!'); window.location.reload();
    await page.waitForLoadState('networkidle');
    
    // Verify exported badge
    await expect(page.locator('span', { hasText: 'Exported' })).toBeVisible(); 
    
    // The button should disappear.
    await expect(exportBtn).toBeHidden();
  });

});
