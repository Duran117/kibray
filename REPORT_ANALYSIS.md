# Audit Report — Kibray (snapshot)

Date: 2025-11-28
Branch: `copilot/improve-repo-governance-and-quality`

Resumen ejecutivo
------------------
- Ejecuté un análisis reproducible sobre la copia local del repositorio. Tests: 602 ejecutados (600 passed, 2 skipped). Cobertura general: 58.4% (líneas cubiertas 8107/13881). Seguridad de dependencias: se detectaron vulnerabilidades en `Django==5.2.4` (varios CVE, ver sección) y en `requests==2.32.3` (CVE que sugiere 2.32.4). Bandit no reportó errores de parsing y produjo `reports/bandit.json` (sin errores críticos en código propio por ahora).

Prioridades (P1 → P3)
---------------------
P1 - Seguridad de dependencias
- Actualizar `Django` a la versión parcheada dentro de la serie 5.2.x (por ejemplo 5.2.8) o a la versión LTS segura aplicada por el equipo, y `requests` a 2.32.4. Razon: múltiples CVE de inyección SQL/DoS y fuga de credenciales. Prueba: correr la suite completa y validar endpoints críticos (finanzas, auth, import/export).

P2 - Cobertura baja
- Cobertura general 58% — priorizar módulos core financieros, integridad de facturas, tests de i18n (UI) y áreas con lógica de negocio crítica. Meta inicial: elevar al 70% en ciclos cortos añadiendo tests unitarios y de integración para módulos con riesgo financiero.

P3 - Calidad del código y limpieza
- Resolver hallazgos de linter (variables asignadas y no usadas F841, E402 imports after django.setup en scripts, simplificaciones C401). Automatizar en CI: ruff + isort + black en pre-commit o workflow GitHub Actions.

Comandos reproducibles (rápido)
-------------------------------
1. Preparar entorno
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Tests y cobertura
```bash
mkdir -p test-results reports
pytest -q --maxfail=1 --junitxml=test-results/junit.xml
coverage run -m pytest
coverage report -m
coverage html -d reports/coverage_html
```

3. Scans rápidos
```bash
.venv/bin/pip-audit -r requirements.txt -f json -o reports/pip_audit.json
.venv/bin/bandit -r . -f json -o reports/bandit.json
```

Hallazgos concretos (máximo 5, críticos primero)
----------------------------------------------
1) Vulnerabilidades en dependencias (P1)
   - `Django==5.2.4`: múltiples CVE (CVE-2025-57833, CVE-2025-59681, CVE-2025-59682, CVE-2025-64458, CVE-2025-64459). Fix suggested: upgrade to 5.2.8+ (o al menos 5.2.6/5.2.7 según CVE). Afecta filtros y QuerySet.annotate Q-dictionary expansion (SQL injection vectors) y funciones de extract() (path traversal).
   - `requests==2.32.3`: CVE-2024-47081 — upgrade to 2.32.4 to fix URL parsing/.netrc credential leakage.

2) Cobertura baja en líneas críticas (P2)
   - Cobertura global: 58.4% (reports/coverage.xml). Recomiendo priorizar tests para: `core/models.py` (finanzas), `core/views_financial.py`, `core/api/` y endpoints de facturación.

3) Lint / estilo (P3)
   - Múltiples tests muestran variables asignadas y no usadas (F841). Revisar tests y eliminar variables o usar `_` cuando se ignoran valores.
   - Scripts `verify_connections.py`, `verify_templates.py` tienen imports después de `django.setup()` (E402). Reordenar imports.

4) Archivo con parse error resuelto
   - `core/consumers_fixed.py` presentaba una sintaxis inválida; lo corregí localmente para permitir formato y análisis. Cambios locales generados en `patches/changes.patch`.

5) Repositorio hygiene
   - Añadí `backups/` y `db_backup_*.sqlite3` a `.gitignore` (local edit). Recomiendo revisar otros artefactos grandes (.coverage, .ruff_cache/) para limpiar antes del merge.

Siguientes pasos recomendados (acciones concretas)
-------------------------------------------------
1. (P1) Crear rama `chore/security/upgrade-django-requests` y probar actualizar `Django` a 5.2.8 y `requests` a 2.32.4. Ejecutar tests completos y revisar DB migrations. (Necesito autorización para commits/push: responde "AUTORIZO PUSH" si quieres que cree la rama y abra PR.)
2. (P2) Añadir cobertura incremental: crear tickets/PRs por módulo de baja cobertura con test stubs. Priorizar `core/views_financial.py` y tests de invoice flows.
3. (P3) Añadir CI workflow (GitHub Actions) que ejecute: setup python, install deps, ruff format/check, pytest+coverage, pip-audit, bandit — bloquear PRs que reduzcan coverage y que introduzcan vulnerabilidades conocidas.

Artefactos generados
--------------------
- `inventory.json` — lista completa de archivos (root + sizes).
- `reports/pip_audit.json`, `reports/bandit.json`, `reports/coverage.xml`, `test-results/junit.xml` — ya presentes.
- `patches/changes.patch` — diff con los cambios locales (consumers + .gitignore).
- `report.json` — resumen métrico (junto a este archivo).

Contacto y notas finales
-----------------------
Si me autorizas, puedo (a) crear la rama para las actualizaciones de seguridad y abrir PR draft, (b) aplicar correcciones de lint y tests / pequeñas mejoras de cobertura por módulos de alto riesgo.
