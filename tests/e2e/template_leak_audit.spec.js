// @ts-check
/**
 * Template-leak audit.
 *
 * Catches Django/Jinja template syntax that escaped the template engine and
 * is being rendered to the user as plain text. Most common cause: multi-line
 * `{# ... #}` comments — Django's `{# #}` is single-line only, so newlines
 * inside leak the entire block as visible text.
 *
 * For each route in ROUTES, this spec:
 *   1. Loads the page (skips 4xx/5xx).
 *   2. Reads `document.body.innerText`.
 *   3. Asserts none of these tokens appear as visible text:
 *        - `{# `  (Django comment open)
 *        - ` #}`  (Django comment close)
 *        - `{% comment %}` / `{% endcomment %}`
 *        - `{% if `, `{% for `, `{% endif %}`, `{% endfor %}`, `{% block `
 *        - `{{ ` and ` }}` (variable interpolation)
 *
 * If any token is found, fails with the surrounding 80-char context so the
 * next agent knows which page/template to fix.
 */

import { test, expect } from '@playwright/test';

const ROUTES = [
  '/dashboard/',
  '/dashboard/admin/',
  '/dashboard/pm/',
  '/dashboard/employee/',
  '/projects/',
  '/projects/1/',
  '/projects/1/tasks/',
  '/projects/1/rfis/',
  '/projects/1/risks/',
  '/projects/1/damages/',
  '/projects/1/inventory/',
  '/tasks/',
  '/invoices/',
  '/clients/',
  '/payroll/week/',
  '/payroll/history/',
  '/incomes/',
  '/planning/list/',
  '/inventory/low-stock/',
  '/organizations/',
  '/pm-calendar/',
];

// Tokens that should NEVER appear as visible text on a rendered page.
// We avoid bare `{%`/`%}` because legitimate code snippets in docs may use
// them; instead we look for the keyword forms which are unambiguously
// template-engine artifacts that leaked.
const FORBIDDEN_TOKENS = [
  '{# ',
  ' #}',
  '{#\n',
  '{% comment %}',
  '{% endcomment %}',
  '{% if ',
  '{% for ',
  '{% endif %}',
  '{% endfor %}',
  '{% block ',
  '{% endblock',
  '{% load ',
  '{% url ',
  '{% trans ',
  '{% static ',
  '{% include ',
  '{{ ',
];

test.describe('Template-leak audit', () => {
  for (const path of ROUTES) {
    test(`route ${path} — no leaked template syntax in visible text`, async ({ page }) => {
      const resp = await page.goto(path, { waitUntil: 'domcontentloaded' });
      if (!resp || resp.status() >= 400) {
        test.skip(true, `route ${path} returned ${resp ? resp.status() : 'no response'}`);
      }

      const text = await page.evaluate(() => document.body.innerText || '');

      const hits = [];
      for (const tok of FORBIDDEN_TOKENS) {
        let idx = text.indexOf(tok);
        while (idx !== -1) {
          const start = Math.max(0, idx - 40);
          const end = Math.min(text.length, idx + tok.length + 40);
          hits.push({
            token: tok,
            context: text.slice(start, end).replace(/\s+/g, ' ').trim(),
          });
          if (hits.length >= 5) break; // cap diagnostic noise
          idx = text.indexOf(tok, idx + tok.length);
        }
        if (hits.length >= 5) break;
      }

      if (hits.length) {
        const msg = hits
          .map(h => `  • leaked "${h.token}" at: …${h.context}…`)
          .join('\n');
        throw new Error(
          `Template syntax leaked into visible page text on ${path}:\n${msg}\n\n` +
          `Hint: Django's {# … #} comments are SINGLE-LINE only — multi-line ` +
          `comments leak the entire block. Use {% comment %} … {% endcomment %} ` +
          `for multi-line. For {{ }} or {% %} leaks, check that {% load %} tags ` +
          `are present and the template extends base_modern.html.`
        );
      }
    });
  }
});
