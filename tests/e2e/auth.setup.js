import { test as setup } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';

/**
 * Global auth setup: seeds a superuser and saves authenticated storage state.
 */
setup('authenticate', async ({ page, context }) => {
  // Ensure admin user exists
  const repoRoot = process.cwd();
  const managePy = path.join(repoRoot, 'manage.py');
  const createCmd = `python3 ${managePy} shell -c "from django.contrib.auth import get_user_model; User=get_user_model();\nusername='admin_playwright';\npassword='admin123';\nif not User.objects.filter(username=username).exists():\n    User.objects.create_superuser(username=username, email='admin_playwright@test.com', password=password)\nelse:\n    u=User.objects.get(username=username);\n    u.is_staff=True; u.is_superuser=True; u.set_password(password); u.save()"`;
  execSync(createCmd, { stdio: 'inherit' });

  // Login via UI to obtain session cookie
  await page.goto('/login/?next=/');
  await page.fill('input[name="username"]', 'admin_playwright');
  await page.fill('input[name="password"]', 'admin123');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"], input[type="submit"]'),
  ]);

  // Save authenticated state
  await context.storageState({ path: 'auth.json' });
});
