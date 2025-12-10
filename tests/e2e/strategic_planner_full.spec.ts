import { test, expect, Page } from '@playwright/test';

const ADMIN_USER = 'admin';
const ADMIN_PASS = 'Kibray2025!Admin';

test.describe('Strategic Planner Full Features', () => {
  
  async function login(page: Page) {
    await page.goto('/login/');
    await page.fill('input[name="username"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PASS);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  }

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Can assign employees and set location for items', async ({ page }) => {
    // 1. Create a new session
    await page.goto('/planner/strategic/');
    await page.click('text=New Planning Session');
    await expect(page.locator('#createSessionModal')).toBeVisible();
    
    // Select project (Test Project Full should be there)
    const projectSelect = page.locator('select[name="project"]');
    await projectSelect.click();
    
    // Wait for the option to be present in the DOM
    const option = page.locator('select[name="project"] option', { hasText: 'Test Project Full' });
    await option.waitFor({ state: 'attached', timeout: 5000 });
    
    await projectSelect.selectOption({ label: 'Test Project Full' });
    
    // Set dates - Use random future dates to avoid collision
    const today = new Date();
    // Use a large random range (up to 10000 days) to minimize collision probability
    const randomOffset = Math.floor(Math.random() * 10000) + 10; 
    const startDay = new Date(today);
    startDay.setDate(today.getDate() + randomOffset);
    const startStr = startDay.toISOString().split('T')[0];
    
    const endDay = new Date(startDay);
    endDay.setDate(startDay.getDate() + 4);
    const endStr = endDay.toISOString().split('T')[0];

    await page.fill('input[name="start_date"]', startStr);
    await page.fill('input[name="end_date"]', endStr);
    await page.click('button:has-text("Create Session")');
    
    // Wait for redirect to detail
    await expect(page).toHaveURL(/\/planner\/strategic\/\d+\//);

    // 2. Add an Item with Location and Assignments
    // Find the first "Add Item" button (for the first day)
    await page.locator('button:has-text("Add Item")').first().click();
    await expect(page.locator('#addItemModal')).toBeVisible();

    await page.fill('#addItemForm input[name="title"]', 'Kitchen Renovation');
    await page.fill('#addItemForm input[name="location_area"]', 'Main Kitchen');
    
    // Select employees (John and Jane)
    // Hold Meta/Control to select multiple? Playwright selectOption handles array
    await page.locator('#addItemForm select[name="assigned_to"]').selectOption([
        { label: 'John Doe' },
        { label: 'Jane Smith' }
    ]);

    await page.locator('#addItemModal button:has-text("Add Item")').click();
    
    // 3. Verify Item Card
    const itemCard = page.locator('.group', { hasText: 'Kitchen Renovation' });
    await expect(itemCard).toBeVisible();
    await expect(itemCard).toContainText('Main Kitchen');
    // Check for avatars (initials)
    await expect(itemCard).toContainText('JD'); // John Doe
    await expect(itemCard).toContainText('JS'); // Jane Smith

    // 4. Add a Task with Assignments
    // Hover to see "Task" button
    await itemCard.hover();
    await itemCard.locator('button:has-text("Task")').click();
    await expect(page.locator('#addTaskModal')).toBeVisible();

    await page.fill('#addTaskForm input[name="description"]', 'Install Cabinets');
    await page.locator('#addTaskForm select[name="assigned_to"]').selectOption([
        { label: 'Bob Builder' }
    ]);
    
    await page.locator('#addTaskModal button:has-text("Add Task")').click();

    // 5. Verify Task
    // We don't show task assignments on the card yet in the preview, but we should verify it was added without error
    await expect(page.locator('text=Install Cabinets')).toBeVisible();

    // 6. Add Material
    // Hover to see "Material" button
    await itemCard.hover();
    await itemCard.locator('button:has-text("Material")').click();
    await expect(page.locator('#addMaterialModal')).toBeVisible();

    await page.fill('#addMaterialForm input[name="name"]', 'Plywood Sheets');
    await page.fill('#addMaterialForm input[name="quantity"]', '10');
    await page.fill('#addMaterialForm input[name="unit"]', 'pcs');
    
    await page.locator('#addMaterialModal button:has-text("Add Material")').click();

    // 7. Verify Material
    await expect(page.locator('text=Plywood Sheets')).toBeVisible();
    // Quantity might be 10 or 10.00 depending on formatting
    await expect(page.locator('text=/10(\\.00)? pcs/')).toBeVisible();
  });
});
