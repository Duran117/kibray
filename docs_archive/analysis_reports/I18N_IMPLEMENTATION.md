# Internationalization (i18n) Implementation

This document describes the bilingual internationalization (English, Spanish) added to Kibray across the frontend and backend.

## Frontend (React)

- Library: `react-i18next`, `i18next`, `i18next-browser-languagedetector`, `i18next-http-backend`
- Config: `frontend/navigation/src/i18n.js`
  - Language detection order: localStorage → navigator → htmlTag → cookie
  - Caching: localStorage, cookie
  - Fallback: `en`
  - Accessibility: Sync `<html lang>` on language change
- Translations: JSON files per language
  - `frontend/navigation/src/locales/en/translation.json`
  - `frontend/navigation/src/locales/es/translation.json`
- Components updated to use `useTranslation` and `t()`:
  - Sidebar (with LanguageSelector)
  - Breadcrumbs
  - ProjectSelector
  - DashboardPM
  - FileManager (+ date/number formatting utils)
  - NotificationCenter
  - Chat MessageList timestamps localized
- Utilities:
  - `formatDate(date, pattern)` locale-aware with date-fns
  - `formatCurrency(amount)` and `formatNumber(value)` using Intl
- Language Selector:
  - `frontend/navigation/src/components/navigation/LanguageSelector.jsx`
  - Writes preference to localStorage and persists to backend `/api/v1/users/preferred_language/`
- WebSocket language propagation:
  - `lang` query parameter added in WS URL for backend localization

## Backend (Django)

- Settings:
  - `USE_I18N = True`, `LANGUAGES = [('en', 'English'), ('es', 'Español')]`
  - `LOCALE_PATHS = [BASE_DIR / 'locale']`
  - `LocaleMiddleware` enabled
  - Custom `LanguageQueryMiddleware` to honor `?lang` or `X-Language` header
- Models:
  - `Profile.language` (preferred UI language) already present; default 'en'
- API:
  - Endpoint to update preference: `PATCH /api/v1/users/preferred_language/`
- WebSockets:
  - Consumers accept `?lang` and activate translation
  - User-facing WS strings use `gettext` (e.g., rate limit error, connection message)
- Translations:
  - `locale/en/LC_MESSAGES/django.po`, `locale/es/LC_MESSAGES/django.po` generated

## How to add a new language

1. Frontend: Add `src/locales/<lng>/translation.json` and extend `resources` in `i18n.js`.
2. Backend: Add to `LANGUAGES` in settings and run:
   - `python manage.py makemessages -l <lng>`
   - Translate `locale/<lng>/LC_MESSAGES/django.po`
   - `python manage.py compilemessages`

## Usage guidelines

- Always wrap user-visible text with `t('key.path')` in React.
- For complex content with markup, use `<Trans i18nKey="key">`.
- For backend messages (errors, emails, logs to users), wrap with `gettext`/`gettext_lazy`.
- Prefer semantic keys grouped by domain: `common`, `navigation`, `files`, `users`, `chat`, etc.

## Pluralization

Use i18next and Django built-in pluralization. Example (i18next):

```
notifications: {
  unread_count_zero: "No unread notifications",
  unread_count_one: "1 unread notification",
  unread_count_other: "{{count}} unread notifications"
}
```

Call with count: `t('notifications.unread_count', { count })` if you define a single key; or use the explicit zero/one/other keys as provided here.

## Performance

- Lazy loading supported via i18next-http-backend (`/locales/{{lng}}/{{ns}}.json`); bundled en/es provided inline for fast startup.
- Caching via localStorage and cookie to avoid re-detection on each load.

## Testing

- Switch language in the UI via the LanguageSelector.
- Verify dates and numbers in components (Chat timestamps, Notification times, FileManager lists) are localized.
- For API, send `Accept-Language: es` or `?lang=es` to receive localized messages.

