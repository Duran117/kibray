# E2E Test Suite

Playwright end-to-end tests for the Kibray Django + React app.

## Quick Start

```bash
# Install once
npm install
npx playwright install --with-deps

# Run the root suite (chromium + firefox + webkit)
npm run test:e2e

# Run only the frontend (React) suite (chromium-only)
npm run test:e2e:frontend

# View HTML report after a run
npm run test:e2e:report
```

The Django server is auto-started by Playwright via `webServer` in each
config; an existing server on `localhost:8000` is reused.

## Two Suites

| Suite | Config | Tests | Browsers |
|---|---|---|---|
| Root | `playwright.config.js` | `tests/e2e/*.spec.{js,ts}` | chromium / firefox / webkit |
| Frontend | `frontend/playwright.config.ts` | `frontend/tests/e2e/*.spec.ts` | chromium |

## Authentication

All credentials live in **`tests/e2e/_helpers/auth.js`**:

```js
import { ADMIN_USER, ADMIN_PASS, loginAsAdmin } from './_helpers/auth.js';
```

Override per environment:

```bash
E2E_ADMIN_USER=alice E2E_ADMIN_PASS='S3cret!' npm run test:e2e
```

The root suite uses `auth.setup.js` to seed the admin user and save a
`storageState` to `auth.json`; chromium/firefox/webkit projects then reuse
that state.

The frontend suite (`frontend/tests/e2e`) currently logs in inline per
spec. Migrating those specs to a shared storageState is tracked in
`docs/E2E_REVIEW.md` (recommendation E1.3.a).

## Environment overrides

| Variable | Default | Purpose |
|---|---|---|
| `E2E_ADMIN_USER` | `admin_playwright` | Admin username for setup + login |
| `E2E_ADMIN_PASS` | `admin123` | Admin password (USE A REAL VALUE IN CI) |
| `PYTHON` | `python3` | Python interpreter for `manage.py runserver` (frontend config) |
| `DJANGO_PORT` | `8000` | Port for the auto-started Django server (frontend config) |
| `CI` | unset | When set: forbid `.only`, retries=2, workers=1 |

## Tagging convention (recommended)

Use `@smoke` in the test title to mark fast-stable tests for the smoke
subset (run via `npm run test:e2e:smoke`):

```ts
test('dashboard loads @smoke', async ({ page }) => { /* ... */ });
```

## Troubleshooting

- **`auth.json` missing** → run the `setup` project once (`npm run test:e2e`
  invokes it automatically).
- **Tests fail with `project_id=1` not found** → seed via fixtures or use a
  fresh test database; some specs assume id=1 exists (see E2E_REVIEW M6).
- **Ports busy** → `lsof -i :8000` then kill, or set `DJANGO_PORT=8001`.
- **Browsers missing** → `npx playwright install --with-deps`.

## Related Docs

- `docs/E2E_REVIEW.md` — full static review of the suite
- `docs/PHASE_E_COMPLETION_REPORT.md` — Phase E summary
