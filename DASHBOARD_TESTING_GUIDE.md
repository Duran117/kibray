# Dashboard Testing & Integration Guide

## Overview
Comprehensive guide for testing the Analytics Dashboard and integrating remaining UI components.

**Status**: Dashboard UI complete, backend tested (23/23 tests passing), ready for integration testing

---

## Analytics Dashboard Testing

### 1. Backend API Endpoints (✅ All Tested - 23/23 Passing)

#### Test Coverage:
- **Project Health Dashboard**: 3 tests
  - Success case with comprehensive metrics
  - 404 error handling for invalid project
  - Unauthenticated access rejection

- **Touchup Analytics Dashboard**: 5 tests
  - Global analytics (all projects)
  - Project-specific filtering
  - Empty dataset handling
  - Unauthenticated access rejection
  - 30-day trends validation

- **Color Approval Analytics Dashboard**: 5 tests
  - Success case with status breakdown
  - Project-specific filtering
  - Empty dataset handling
  - Unauthenticated access rejection
  - Pending aging calculation

- **PM Performance Dashboard**: 5 tests
  - Admin access success
  - Regular user 403 forbidden
  - Unauthenticated access rejection
  - Empty dataset handling
  - Staff user access allowed

- **Edge Cases**: 4 tests
  - Zero budget handling
  - Touchup completion rate accuracy
  - Brand top 10 limit enforcement
  - PM completion rate accuracy

- **Performance**: 1 test
  - Query efficiency (8 queries for project health - excellent!)

#### Run Backend Tests:
```bash
cd /Users/jesus/Documents/kibray
pytest tests/test_analytics_dashboards.py -v
```

**Expected**: All 23 tests pass with query performance validation

---

### 2. Frontend Dashboard Component

#### Component Structure:
- **Location**: `frontend/src/pages/Dashboard.tsx`
- **Entry Point**: `frontend/src/dashboard-main.tsx`
- **Built Asset**: `staticfiles/gantt/dashboard.BuT8jHGj.js` (418KB)

#### Features Implemented:
✅ 4-tab navigation (Project Health, Touch-ups, Color Approvals, PM Performance)
✅ Recharts visualizations (Pie, Bar, Line charts)
✅ Project filter input with optional filtering
✅ KPI cards with color-coded metrics
✅ API integration with JWT authentication
✅ Loading states with spinner
✅ Error handling with user-friendly messages
✅ Responsive design with Tailwind CSS
✅ Admin permission checks for PM Performance tab
✅ Risk indicators for project health

#### TypeScript Quality:
✅ All TypeScript errors resolved
✅ Type declarations for frappe-gantt
✅ Proper interface definitions for analytics data
✅ Clean separation of concerns

---

## Integration Testing Steps

### Step 1: Start Django Development Server
```bash
cd /Users/jesus/Documents/kibray
python manage.py runserver
```

### Step 2: Navigate to Analytics Dashboard
```
http://localhost:8000/dashboard/analytics/
```

### Step 3: Manual Test Checklist

#### A. Project Health Tab
- [ ] Enter a valid project ID (e.g., 1)
- [ ] Verify completion percentage displays correctly
- [ ] Check budget remaining KPI card shows accurate amount
- [ ] Validate timeline status badge (On Track / Behind Schedule)
- [ ] Count overdue tasks KPI matches actual
- [ ] Pie chart renders with task distribution (Completed/In Progress/Pending/Cancelled)
- [ ] Bar chart shows budget (Spent vs Remaining)
- [ ] Risk indicators appear if:
  - [ ] Budget overrun detected
  - [ ] Project behind schedule
  - [ ] Overdue tasks > 0
- [ ] Try invalid project ID → verify 404 error message
- [ ] Clear project ID → verify "Enter a Project ID" message

#### B. Touch-ups Tab
- [ ] Leave project ID empty → verify global analytics load
- [ ] Check total touch-ups KPI card
- [ ] Verify completion rate percentage
- [ ] Validate avg resolution time in hours
- [ ] Bar chart displays status distribution
- [ ] Pie chart shows priority breakdown with colors
- [ ] Line chart renders 30-day trends
- [ ] Enter specific project ID → verify filtered results
- [ ] Try project with no touch-ups → verify zero metrics display

#### C. Color Approvals Tab
- [ ] Leave project ID empty → verify global analytics load
- [ ] Check total approvals KPI
- [ ] Verify pending count
- [ ] Validate avg approval time
- [ ] Check oldest pending age in days
- [ ] Pie chart displays status (PENDING/APPROVED/REJECTED)
- [ ] Bar chart shows top 10 brands with counts
- [ ] Enter specific project ID → verify filtered results
- [ ] Try project with no approvals → verify zero metrics display

#### D. PM Performance Tab
- [ ] **Admin/Staff User**: 
  - [ ] Tab accessible
  - [ ] KPI cards show: Total PMs, Avg Projects per PM, Avg Completion Rate
  - [ ] Bar chart displays PM completion rates
  - [ ] Table shows detailed PM metrics (projects, tasks, completion %, overdue)
  - [ ] Table rows color-coded by completion rate (green ≥80%, yellow ≥60%, red <60%)
- [ ] **Regular User**:
  - [ ] Attempt to access tab
  - [ ] Verify "Admin access required" error message appears
- [ ] Try with no PM assignments → verify zero metrics display

#### E. Cross-Cutting Concerns
- [ ] Loading spinner appears during API calls
- [ ] Error messages display properly for failed requests
- [ ] Tab switching works smoothly
- [ ] Project filter input accepts numbers only
- [ ] Charts responsive on different screen sizes
- [ ] Tooltips appear on chart hover
- [ ] All charts render without console errors

---

### Step 4: Browser Console Checks

Open browser DevTools (F12) and verify:
- [ ] No JavaScript errors in console
- [ ] Network tab shows successful API calls:
  - [ ] `/api/v1/analytics/projects/{id}/health/` (200 OK)
  - [ ] `/api/v1/analytics/touchups/?project={id}` (200 OK)
  - [ ] `/api/v1/analytics/color-approvals/?project={id}` (200 OK)
  - [ ] `/api/v1/analytics/pm-performance/` (200 OK or 403 if not admin)
- [ ] JWT token in Authorization header for all requests
- [ ] Response payloads match expected structure

---

### Step 5: Performance Validation

Check Network tab metrics:
- [ ] Dashboard JS bundle size: ~418KB (acceptable for comprehensive dashboard)
- [ ] API response times < 500ms for all endpoints
- [ ] Charts render within 1 second of data load
- [ ] No memory leaks on tab switching (use Performance Monitor)

---

## End-to-End Testing with Playwright

### Prerequisites:
Playwright already installed in `frontend/package.json` devDependencies

### Run E2E Tests:
```bash
cd /Users/jesus/Documents/kibray/frontend
npm run test:e2e
```

### E2E Test Coverage (Phase 4):
- Touch-up Board workflows
- Color Approval request/approve/reject flows
- PM Assignment creation and notifications
- Notification Center interactions

### TODO: Add Dashboard E2E Tests
Create `frontend/tests/e2e/dashboard.spec.ts`:
- Navigate to /dashboard/analytics/
- Test each tab with sample data
- Verify chart rendering
- Test project filtering
- Validate error states
- Check admin-only access

---

## Remaining UI Integration

### 1. Touch-up Board Page
**File**: `frontend/src/pages/TouchupBoard.tsx` (✅ Created)

**Integration Steps**:
- [ ] Create Django template: `core/templates/core/touchup_board_react.html`
- [ ] Add view in `core/views.py`: `touchup_board_react(request, project_id)`
- [ ] Wire route: `/projects/<int:project_id>/touchups-react/`
- [ ] Create Vite entry: `frontend/src/touchup-main.tsx`
- [ ] Build and test

**Template Pattern**:
```html
{% extends 'core/base.html' %}
{% load static %}
{% block content %}
<div id="touchup-root" data-project-id="{{ project_id }}"></div>
{% endblock %}
{% block extra_js %}
{% if DEBUG %}
    <script type="module" src="http://localhost:5173/@vite/client"></script>
    <script type="module" src="http://localhost:5173/src/touchup-main.tsx"></script>
{% else %}
    <script type="module" src="{% static 'gantt/touchup.{hash}.js' %}"></script>
{% endif %}
{% endblock %}
```

### 2. Color Approvals Page
**File**: `frontend/src/pages/ColorApprovals.tsx` (✅ Created)

**Integration Steps**:
- [ ] Create Django template: `core/templates/core/color_approvals_react.html`
- [ ] Add view: `color_approvals_react(request)`
- [ ] Wire route: `/color-approvals-react/`
- [ ] Add file upload handling for client signature
- [ ] Create Vite entry: `frontend/src/approvals-main.tsx`
- [ ] Build and test

**File Upload Feature**:
```typescript
// In ColorApprovals.tsx, add:
const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (file) {
    const formData = new FormData();
    formData.append('client_signature', file);
    // ... rest of form data
    axios.post('/api/v1/color-approvals/', formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};
```

### 3. PM Assignments Page
**File**: `frontend/src/pages/PMAssignments.tsx` (✅ Created)

**Integration Steps**:
- [ ] Create Django template: `core/templates/core/pm_assignments_react.html`
- [ ] Add view: `pm_assignments_react(request)`
- [ ] Wire route: `/pm-assignments-react/`
- [ ] Create Vite entry: `frontend/src/pm-main.tsx`
- [ ] Build and test

### 4. Notification Center (Global Header Integration)
**File**: `frontend/src/pages/NotificationCenter.tsx` (✅ Created)

**Integration Pattern**:
Since this is a global component, integrate into Django base template:

```html
<!-- core/templates/core/base.html -->
{% block extra_js %}
<!-- Add after other scripts -->
{% if user.is_authenticated %}
<div id="notification-center-root"></div>
<script type="module" src="{% static 'gantt/notifications.{hash}.js' %}"></script>
{% endif %}
{% endblock %}
```

**Position with CSS**:
```css
#notification-center-root {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}
```

---

## Build Process for All UI Components

### Update vite.config.ts:
```typescript
rollupOptions: {
  input: {
    main: './src/main.tsx',
    dashboard: './src/dashboard-main.tsx',
    touchup: './src/touchup-main.tsx',
    approvals: './src/approvals-main.tsx',
    pm: './src/pm-main.tsx',
    notifications: './src/notifications-main.tsx'
  },
  output: {
    entryFileNames: '[name].[hash].js',
    chunkFileNames: '[name].[hash].js',
    assetFileNames: '[name].[hash].[ext]'
  }
}
```

### Build All Entries:
```bash
cd frontend
npm run build
```

### Verify Built Assets:
```bash
ls -lah ../staticfiles/gantt/ | grep -E "(dashboard|touchup|approvals|pm|notifications)"
```

---

## Troubleshooting

### Issue: TypeScript Compilation Errors
**Solution**: Check for:
- Unused imports (remove with `import { used } from 'module'`)
- Implicit any types (add type annotations)
- Missing type declarations (create `.d.ts` files)

### Issue: Vite Build Fails with SCSS Error
**Solution**: 
```bash
npm install -D sass-embedded
```

### Issue: Dashboard Not Loading in Browser
**Checks**:
1. Verify Django collectstatic ran: `python manage.py collectstatic --noinput`
2. Check template loads correct hashed filename
3. Inspect Network tab for 404 errors on JS bundle
4. Verify `STATIC_ROOT` and `STATICFILES_DIRS` in settings.py

### Issue: API 401 Unauthorized
**Checks**:
1. Verify JWT token in localStorage: `localStorage.getItem('token')`
2. Check Authorization header in Network tab
3. Confirm token hasn't expired
4. Try refreshing token or re-logging in

### Issue: Charts Not Rendering
**Checks**:
1. Open console for React errors
2. Verify recharts installed: `npm list recharts`
3. Check data structure matches component expectations
4. Inspect element - chart container should have dimensions

---

## Performance Benchmarks

### Backend Query Performance:
- **Project Health**: 8 queries (excellent efficiency)
- **Touch-up Analytics**: ~5-10 queries depending on dataset size
- **Color Approval Analytics**: ~5-10 queries
- **PM Performance**: ~10-15 queries (acceptable for admin dashboard)

### Frontend Bundle Sizes:
- **Dashboard**: 418KB (includes recharts, acceptable)
- **Gantt (main)**: ~250KB (includes frappe-gantt)
- **Shared chunks**: React (130KB), axios, date-fns

**Target**: Page load < 2 seconds on 4G connection

---

## Next Steps After Dashboard Testing

1. **Test Dashboard Integration**: Complete manual checklist above
2. **Fix Any Issues**: Address bugs or UX problems
3. **Integrate Remaining Pages**: TouchupBoard, ColorApprovals, PMAssignments, NotificationCenter
4. **Create Vite Entries**: One main.tsx file per page
5. **Build All Assets**: Run npm run build
6. **Update Django Templates**: Wire all routes and templates
7. **Run E2E Tests**: Validate all workflows
8. **Documentation**: Update API_README.md with frontend routes
9. **Production Deploy**: Ensure collectstatic runs in deployment pipeline

---

## Success Criteria

### Backend:
- ✅ 23/23 tests passing
- ✅ Query performance < 20 queries per endpoint
- ✅ API documented in API_README.md
- ✅ Proper permissions and error handling

### Frontend:
- [ ] Dashboard loads without errors
- [ ] All 4 tabs render correctly with sample data
- [ ] Charts interactive (tooltips, legends work)
- [ ] Project filtering works correctly
- [ ] Admin-only access enforced for PM Performance
- [ ] No TypeScript compilation errors
- [ ] Bundle size acceptable (< 500KB per entry)

### Integration:
- [ ] Django templates load React components
- [ ] Dev/prod mode switching works
- [ ] Static files served correctly
- [ ] API calls authenticated with JWT
- [ ] Error states display user-friendly messages

---

## Contact & Support

**Documentation Files**:
- Backend API: `API_README.md`
- Analytics Implementation: `tests/test_analytics_dashboards.py`
- Dashboard Component: `frontend/src/pages/Dashboard.tsx`
- This Guide: `DASHBOARD_TESTING_GUIDE.md`

**Test Command Summary**:
```bash
# Backend tests
pytest tests/test_analytics_dashboards.py -v

# Frontend build
cd frontend && npm run build

# E2E tests
cd frontend && npm run test:e2e

# Django dev server
python manage.py runserver
```

**Status**: Ready for integration testing. Backend complete and tested, frontend built and committed.
