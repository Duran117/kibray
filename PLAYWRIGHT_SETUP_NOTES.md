# Playwright Setup Notes

## Overview
This project uses Playwright for End-to-End (E2E) testing. The configuration is located in `playwright.config.js`.

## Installation
Playwright and its dependencies should be installed via npm:
```bash
npm install
npx playwright install --with-deps
```

## Running Tests
To run all tests:
```bash
npx playwright test
```

To run only the Strategic Planner tests:
```bash
npx playwright test tests/e2e/strategic_planner.spec.ts
```

## Authentication
The project uses a global setup `tests/e2e/auth.setup.js` which attempts to set an auth token.
However, for Django View testing (which requires session cookies), we use a specific login flow in our tests using the `admin` user.

**Test Credentials:**
- Username: `admin`
- Password: `Kibray2025!Admin`

## Strategic Planner Tests
The Strategic Planner tests are located in `tests/e2e/strategic_planner.spec.ts`.
They cover:
1. Dashboard access
2. Session creation
3. Visual Board access
4. Item and Task creation
5. Drag & Drop functionality
6. Export to Daily Plan

## Environment
Tests assume the Django development server is running at `http://localhost:8000`.
The `playwright.config.js` is configured to start the server automatically using `python3 manage.py runserver`.
