# Contributing Translations

Thank you for helping improve Kibray's internationalization.

## Where to edit translations

- Frontend strings (React):
  - English: `frontend/navigation/src/locales/en/translation.json`
  - Spanish: `frontend/navigation/src/locales/es/translation.json`
- Backend strings (Django):
  - `.po` files in `locale/<lng>/LC_MESSAGES/django.po`

## Tools recommended

- JSON: Any editor with JSON linting (VS Code). Keep keys sorted and consistent.
- Django `.po` files: Poedit or VS Code PO files extension.

## Adding a new key (frontend)

1. Add the key to `en/translation.json` under the appropriate namespace.
2. Mirror the key with a proper translation in `es/translation.json`.
3. Use it in code with `t('namespace.key')`.

## Running the app locally

- Frontend (Navigation):
  - `cd frontend/navigation && npm install && npm run dev`
- Backend:
  - `python manage.py runserver`

## Updating backend translations

1. Mark strings with `gettext` / `gettext_lazy` in Python and Django templates.
2. Generate/update `.po` files:
   - `python manage.py makemessages -l en -l es --ignore=node_modules --ignore=static --no-obsolete`
3. Translate in `locale/*/LC_MESSAGES/django.po`.
4. Compile:
   - `python manage.py compilemessages`

## Style guide (Spanish)

- Use formal "usted" form.
- Prefer construction industry terminology:
  - Gestor de Archivos, Gestión de Usuarios, Cronograma, Presupuesto, Factura, Contratista, Subcontratista, Materiales, Equipo.
- Verify grammar: accents (á, é, í, ó, ú), ñ, punctuation.
- Avoid literal translations; use natural phrasing in context.

## Review checklist

- [ ] English and Spanish keys exist and match structure
- [ ] No hardcoded user-facing strings remain in UI
- [ ] Pluralization forms present where needed (zero/one/other)
- [ ] Dates and numbers render per locale
- [ ] WebSocket and API messages localized

## Submitting

- Open a Pull Request with a clear summary.
- Link screenshots showing UI in both languages when possible.
- Request a review from maintainers.
