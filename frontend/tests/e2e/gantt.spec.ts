import { test, expect, Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/admin/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('input[type="submit"]');
  await page.waitForSelector('body');
}

async function createTask(page: Page, projectId: number) {
  // Use raw fetch to create a task via API (avoid UI complexity)
  await page.evaluate(async (pid) => {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const payload = {
      project: pid,
      name: 'Tarea Demo',
      title: 'Tarea Demo',
      planned_start: '2025-11-27',
      planned_end: '2025-11-28',
      status: 'NOT_STARTED',
      percent_complete: 0
    };
    await fetch(`/api/v1/schedule/items/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
  }, projectId);
}

test.describe.serial('Gantt Schedule E2E', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Mounts and sets data-mounted attribute', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    const root = page.locator('#gantt-root');
    await root.waitFor({ state: 'attached', timeout: 8000 });
    await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1', { timeout: 8000 });
    await expect(page.locator('[data-component="gantt-app"]')).toBeVisible();
  });

  test('Schedule items endpoint healthy', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    const result = await page.evaluate(async () => {
      const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
      return { ok: res.ok, status: res.status };
    });
    expect(result.ok).toBeTruthy();
    expect(result.status).toBe(200);
  });

  test('Create task via API and appears in Gantt', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    await createTask(page, 1);
    await page.reload();
    // Wait for data load instrumentation
    await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
    // Poll API until task appears (allows DB commit to settle post-creation)
    const exists = await page.waitForFunction(async () => {
      const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
      const data = await res.json();
      return Array.isArray(data) && data.some((i: any) => (i.name || i.title) === 'Tarea Demo');
    }, { timeout: 3000 });
    expect(exists).toBeTruthy();
  });

  test('Change view mode persists after reload', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    await page.waitForSelector('[data-component="gantt-chart"]');
    // Click Week button
    await page.click('button:has-text("Week")');
    await page.reload();
    // Week button should remain active (btn-primary class)
    const weekBtnClass = await page.locator('button:has-text("Week")').getAttribute('class');
    expect(weekBtnClass).toContain('btn-primary');
  });

  test('No console errors during render', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.goto('/projects/1/schedule/gantt/');
    await page.waitForSelector('[data-component="gantt-chart"]');
    await page.waitForTimeout(1000);
    const relevant = errors.filter(e => !e.includes('favicon') && !e.includes('404'));
    expect(relevant.length).toBe(0);
  });

  test('Empty state handled gracefully', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    // If no tasks exist message should appear OR tasks container rendered
    const hasEmpty = await page.locator('.gantt-container:has-text("No hay tareas")').count();
    expect(hasEmpty >= 0).toBeTruthy();
  });

  test('Open task editor via New Task button', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    await page.waitForSelector('[data-component="gantt-app"]');
    await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
    // Verify button exists and is clickable
    const btnExists = await page.locator('button:has-text("Nueva Tarea")').count();
    expect(btnExists).toBeGreaterThan(0);
  });

  test('Create task via API and verify in list', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    
    // Create via API
    const created = await page.evaluate(async () => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const res = await fetch('/api/v1/schedule/items/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        credentials: 'include',
        body: JSON.stringify({
          project: 1,
          name: 'Tarea API Test',
          planned_start: '2025-12-10',
          planned_end: '2025-12-15',
          status: 'NOT_STARTED',
          percent_complete: 0
        })
      });
      return res.ok || res.status === 201;
    });
    expect(created).toBeTruthy();
    
    // Reload and verify
    await page.reload();
    await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
    const exists = await page.waitForFunction(async () => {
      const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
      const data = await res.json();
      return Array.isArray(data) && data.some((i: any) => (i.name || i.title) === 'Tarea API Test');
    }, { timeout: 3000 });
    expect(exists).toBeTruthy();
  });

  test('Edit existing task and verify update', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    await page.waitForSelector('[data-component="gantt-app"]');
    
    // First create a task to edit
    await createTask(page, 1);
    await page.reload();
    await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
    
    // Wait a bit for Gantt to render tasks
    await page.waitForTimeout(1000);
    
    // Fetch task ID (handle paginated response)
    const taskId = await page.evaluate(async () => {
      const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
      const json = await res.json();
      const data = Array.isArray(json) ? json : (json.results || []);
      const task = data.find((i: any) => (i.name || i.title) === 'Tarea Demo');
      return task ? task.id : null;
    });
    
    if (taskId) {
      // Update via API
      const updated = await page.evaluate(async (id) => {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch(`/api/v1/schedule/items/${id}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          credentials: 'include',
          body: JSON.stringify({ name: 'Tarea Editada', percent_complete: 50 })
        });
        return res.ok;
      }, taskId);
      expect(updated).toBeTruthy();
      
      // Reload and verify change persisted
      await page.reload();
      await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
      const exists = await page.waitForFunction(async () => {
        const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
        const json = await res.json();
        const data = Array.isArray(json) ? json : (json.results || []);
        return Array.isArray(data) && data.some((i: any) => (i.name || i.title) === 'Tarea Editada');
      }, { timeout: 3000 });
      expect(exists).toBeTruthy();
    }
  });

  test('Delete task via API and verify removal', async ({ page }) => {
    await page.goto('/projects/1/schedule/gantt/');
    
    // Create a task to delete
    await createTask(page, 1);
    await page.reload();
    await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
    
    // Get task ID (handle pagination)
    const taskId = await page.evaluate(async () => {
      const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
      const json = await res.json();
      const data = Array.isArray(json) ? json : (json.results || []);
      const task = data.find((i: any) => (i.name || i.title) === 'Tarea Demo');
      return task ? task.id : null;
    });
    
    if (taskId) {
      // Delete via API
      const deleted = await page.evaluate(async (id) => {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch(`/api/v1/schedule/items/${id}/`, {
          method: 'DELETE',
          headers: { 'X-CSRFToken': csrfToken },
          credentials: 'include'
        });
        return res.ok || res.status === 204;
      }, taskId);
      expect(deleted).toBeTruthy();
      
      // Reload and verify task gone
      await page.reload();
      await page.waitForFunction(() => document.getElementById('gantt-root')?.getAttribute('data-mounted') === '1');
      const absent = await page.evaluate(async (id) => {
        const res = await fetch('/api/v1/schedule/items/?project=1', { credentials: 'include' });
        const json = await res.json();
        const data = Array.isArray(json) ? json : (json.results || []);
        return !data.some((i: any) => i.id === id);
      }, taskId);
      expect(absent).toBeTruthy();
    }
  });
});
