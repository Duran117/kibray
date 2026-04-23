import { test as setup } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';
import { ADMIN_USER, ADMIN_PASS } from './_helpers/auth.js';

/**
 * Global auth setup: seeds a superuser and saves authenticated storage state.
 * Credentials come from tests/e2e/_helpers/auth.js (env-overridable).
 */
setup('authenticate', async ({ page, context }) => {
  // Ensure admin user exists
  const repoRoot = process.cwd();
  const managePy = path.join(repoRoot, 'manage.py');
  const createCmd = `python3 ${managePy} shell -c "from django.contrib.auth import get_user_model; User=get_user_model();\nusername='${ADMIN_USER}';\npassword='${ADMIN_PASS}';\nif not User.objects.filter(username=username).exists():\n    User.objects.create_superuser(username=username, email=username+'@test.com', password=password)\nelse:\n    u=User.objects.get(username=username);\n    u.is_staff=True; u.is_superuser=True; u.set_password(password); u.save()"`;
  execSync(createCmd, { stdio: 'inherit' });

  // Login via UI to obtain session cookie
  await page.goto('/login/?next=/');
  await page.fill('input[name="username"]', ADMIN_USER);
  await page.fill('input[name="password"]', ADMIN_PASS);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"], input[type="submit"]'),
  ]);

  // Save authenticated state
  await context.storageState({ path: 'auth.json' });
});
