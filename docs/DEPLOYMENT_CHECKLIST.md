# Deployment Checklist

> **Phase E3 — actionable one-pager.** For full reference architecture see
> [`DEPLOYMENT_MASTER.md`](DEPLOYMENT_MASTER.md). This checklist is what you
> actually run/verify on every production deploy.

**Last reviewed:** April 2026 (Phase E)

---

## 1. Pre-Deploy (local / CI)

- [ ] **Tests green:** `pytest` → expect ≥ 1,255 passing, 0 failed, ≤ 17 skipped
- [ ] **Coverage floor:** `pytest --cov` exits 0 (enforced 35% via `pytest.ini`)
- [ ] **Lint clean:** `ruff check .` exits 0
- [ ] **Format clean:** `black --check .` exits 0
- [ ] **Migrations consistent:** `python manage.py makemigrations --dry-run --check` exits 0
- [ ] **No secret leakage:** `git diff origin/main..HEAD | grep -Ei 'sk_live|pk_live|password\s*='` returns nothing
- [ ] **Static collected (smoke):** `python manage.py collectstatic --noinput --dry-run` succeeds
- [ ] **E2E smoke (optional but recommended):**
      `npm run test:e2e:smoke` (chromium-only) — see [`tests/e2e/README.md`](../tests/e2e/README.md)

## 2. Backup (production)

- [ ] **Snapshot DB before deploy:**
      ```bash
      PGPASSWORD=*** ./scripts/backup_postgres.sh kibray_prod kibray /var/backups/kibray
      ```
- [ ] **Verify backup written:** `ls -lh /var/backups/kibray/kibray_prod-*.sql.gz | tail -1`
- [ ] **Verify gzip integrity:** automatic via `gzip -t` inside script (will exit non-zero on corruption)
- [ ] **Keep ≥ 7 days retention** (cron handles via `scripts/backup_cron.sh`)

## 3. Deploy

- [ ] **Push to main:** `git push origin main` → Railway auto-deploys
- [ ] **Watch build logs** in Railway dashboard until "Deployment successful"
- [ ] **Migrations ran:** check logs for `Applying core.NNNN_… OK`
- [ ] **No errors in startup:** grep logs for `Traceback`, `ERROR`, `CRITICAL`

## 4. Post-Deploy Verification

- [ ] **Health endpoint 200:** `curl -fsS https://<prod-host>/health/ | head`
- [ ] **Login flow:** visit `/login/`, sign in with smoke account, land on dashboard
- [ ] **Critical pages 2xx:**
      - `/dashboard/admin/`
      - `/invoices/`
      - `/invoices/payments/`
      - `/projects/`
- [ ] **API smoke:** `curl -fsS https://<prod-host>/api/v1/dashboards/financial/ -H "Authorization: Bearer <token>"`
- [ ] **No new Sentry issues** in the 5 minutes after deploy
- [ ] **Notify channel:** post commit hash + deploy time

## 5. Rollback Triggers

Roll back immediately if any of:
- 5xx rate > 1% sustained > 2 min
- Login broken
- Payment / invoice mutation endpoints returning 500
- Database connection errors

**Rollback command (Railway):** redeploy previous successful build via dashboard,
or `git revert <bad-sha> && git push origin main`.

If schema migration broke things and rollback needs a DB restore:
```bash
gunzip -c /var/backups/kibray/kibray_prod-<TIMESTAMP>.sql.gz | psql -U kibray kibray_prod
```

## 6. Post-Mortem (only if rollback)

- [ ] File incident note in `docs/incidents/` with timeline, root cause, fix
- [ ] Add regression test covering the failure mode
- [ ] Re-run this checklist before next deploy attempt

---

## Quick reference — env vars

Required in production (Railway → Variables):

| Var | Purpose |
|---|---|
| `SECRET_KEY` | Django secret |
| `DEBUG` | must be `False` |
| `DATABASE_URL` | Postgres DSN |
| `ALLOWED_HOSTS` | comma-sep hostnames |
| `AWS_*` | S3 storage (if used) |
| `SENTRY_DSN` | error tracking (optional but recommended) |
| `EMAIL_*` | SMTP for notifications |

Sanity-check before deploy: `railway variables` (Railway CLI) or the dashboard.
