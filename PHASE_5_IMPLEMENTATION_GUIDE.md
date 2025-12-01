# Phase 5 - Remaining Tasks Implementation Guide

## Quick Start: Complete Frontend Integration

### Current Status:
- ✅ Backend API 100% complete and running
- ✅ JWT authentication utility implemented (`api.js`)
- ✅ Login component created
- ✅ Protected route wrapper created
- ⏳ App routing and widget updates pending

---

## IMMEDIATE NEXT STEPS

### Step 1: Test Backend API (5 minutes)

```bash
# Ensure Django server is running
cd /Users/jesus/Documents/kibray
python3 manage.py runserver

# In another terminal, test authentication:
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"testpass123"}'

# Should return: {"access": "...", "refresh": "..."}

# Test projects endpoint:
curl http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 2: Run Backend Tests (5 minutes)

```bash
cd /Users/jesus/Documents/kibray
python3 manage.py test core.tests.api

# Expected output: Ran 27 tests in X.XXXs, OK
```

### Step 3: Build Frontend (10 minutes)

```bash
cd /Users/jesus/Documents/kibray/frontend/navigation
npm install  # Ensure dependencies
npm run build  # Build production bundle

# Should create: static/js/kibray-navigation.js
```

### Step 4: Collect Static Files (2 minutes)

```bash
cd /Users/jesus/Documents/kibray
python3 manage.py collectstatic --noinput
```

### Step 5: Test Login Flow (5 minutes)

1. Open browser to http://localhost:8000
2. Should redirect to /login
3. Enter credentials: admin / testpass123
4. Click "Sign In"
5. Check browser DevTools:
   - Application > Local Storage: Verify `kibray_access_token` exists
   - Network tab: Verify POST to `/api/v1/auth/token/` returns 200
6. After login, should redirect to dashboard

---

## FILES THAT NEED UPDATES

### Priority 1: App Routing (15 minutes)

**File:** `frontend/navigation/src/App.jsx`

```jsx
import React from 'react';
import Login from './components/auth/Login';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { isAuthenticated } from './utils/api';
import NavigationProvider from './context/NavigationContext';
import RoleProvider from './context/RoleContext';
import ThemeProvider from './context/ThemeContext';
import Sidebar from './components/navigation/Sidebar';
import Breadcrumbs from './components/navigation/Breadcrumbs';
import ProjectSelector from './components/navigation/ProjectSelector';
import './styles/global.css';

function App() {
  const path = window.location.pathname;
  
  // Show login page for /login route
  if (path === '/login') {
    return <Login />;
  }
  
  // Redirect to login if not authenticated
  if (!isAuthenticated()) {
    window.location.href = '/login';
    return null;
  }
  
  // Main app with authentication
  return (
    <ThemeProvider>
      <RoleProvider>
        <NavigationProvider>
          <div className="app-container">
            <Sidebar />
            <div className="main-content">
              <Breadcrumbs />
              <div className="content-header">
                <ProjectSelector />
              </div>
              <div className="page-content">
                {/* Main content area where dashboards render */}
              </div>
            </div>
          </div>
        </NavigationProvider>
      </RoleProvider>
    </ThemeProvider>
  );
}

export default App;
```

### Priority 2: Update ProjectSelector (10 minutes)

**File:** `frontend/navigation/src/components/navigation/ProjectSelector.jsx`

Find the `fetchProjects` function and update:

```jsx
const fetchProjects = async () => {
  setLoading(true);
  try {
    const data = await api.get('/projects/assigned_projects/');
    const projectList = data.results || data;
    setProjects(projectList);
    setFilteredProjects(projectList);
  } catch (error) {
    console.error('Error fetching projects:', error);
    setProjects([]);
    setFilteredProjects([]);
  } finally {
    setLoading(false);
  }
};
```

Remove any `mockApi` imports and usage.

### Priority 3: Update Widgets (30 minutes)

#### AlertsWidget
**File:** `frontend/navigation/src/components/navigation/widgets/AlertsWidget.jsx`

```jsx
const fetchAlerts = async () => {
  setLoading(true);
  try {
    const projectParam = projectId ? `&project=${projectId}` : '';
    const data = await api.get(`/alerts/?ordering=-created_at${projectParam}`);
    setAlerts(data.results || data);
  } catch (error) {
    console.error('Error fetching alerts:', error);
    setAlerts([]);
  } finally {
    setLoading(false);
  }
};
```

#### TasksWidget
**File:** `frontend/navigation/src/components/navigation/widgets/TasksWidget.jsx`

```jsx
const fetchTasks = async () => {
  setLoading(true);
  try {
    const filterParam = filter === 'all' ? '' : 
                       filter === 'completed' ? '&status=Completada' : 
                       '&status__in=En Progreso,Pendiente';
    const projectParam = projectId ? `&project=${projectId}` : '';
    const data = await api.get(`/tasks/?ordering=due_date${filterParam}${projectParam}`);
    setTasks(data.results || data);
  } catch (error) {
    console.error('Error fetching tasks:', error);
    setTasks([]);
  } finally {
    setLoading(false);
  }
};
```

#### ChangeOrdersWidget
**File:** `frontend/navigation/src/components/navigation/widgets/ChangeOrdersWidget.jsx`

```jsx
const fetchChangeOrders = async () => {
  setLoading(true);
  try {
    const projectParam = projectId ? `&project=${projectId}` : '';
    const data = await api.get(`/changeorders/?ordering=-submitted_date${projectParam}`);
    setChangeOrders(data.results || data);
  } catch (error) {
    console.error('Error fetching change orders:', error);
    setChangeOrders([]);
  } finally {
    setLoading(false);
  }
};
```

### Priority 4: Update AnalyticsDashboard (15 minutes)

**File:** `frontend/navigation/src/components/analytics/AnalyticsDashboard.jsx`

Find `fetchAnalytics` and update:

```jsx
const [error, setError] = useState(null);

const fetchAnalytics = async () => {
  setLoading(true);
  setError(null);
  try {
    const data = await api.get(`/nav-analytics/?range=${timeRange}`);
    setAnalyticsData(data);
  } catch (error) {
    console.error('Error fetching analytics:', error);
    setError('Failed to load analytics data. Please try again.');
    setAnalyticsData({
      total_projects: 0,
      active_projects: 0,
      total_tasks: 0,
      completed_tasks: 0,
    });
  } finally {
    setLoading(false);
  }
};
```

Remove `getMockAnalytics` function completely.

Add error display in render:

```jsx
if (error) {
  return (
    <div className="analytics-error">
      <AlertCircle size={48} />
      <h3>Error Loading Analytics</h3>
      <p>{error}</p>
      <button onClick={() => fetchAnalytics()}>Retry</button>
    </div>
  );
}
```

---

## TESTING CHECKLIST

### Backend Tests
```bash
cd /Users/jesus/Documents/kibray
python3 manage.py test core.tests.api -v 2
```
**Expected:** All 27 tests pass

### Frontend Build
```bash
cd frontend/navigation
npm run build
```
**Expected:** Bundle created successfully in `static/js/`

### Manual Testing

#### 1. Authentication Flow
- [ ] Login page appears at `/login`
- [ ] Invalid credentials show error message
- [ ] Valid credentials redirect to dashboard
- [ ] Token stored in localStorage
- [ ] Logout clears tokens and redirects to login

#### 2. API Integration
- [ ] Projects load in ProjectSelector
- [ ] Alerts widget shows real data
- [ ] Tasks widget shows real data with filters working
- [ ] Change orders widget shows real data
- [ ] Analytics dashboard shows real KPIs
- [ ] Time range selector updates dashboard

#### 3. Network Requests
- [ ] No CORS errors in console
- [ ] All requests to `/api/v1/` endpoints
- [ ] Authorization header contains Bearer token
- [ ] 200 OK responses for successful requests
- [ ] 401 triggers automatic token refresh
- [ ] After refresh, request retries successfully

#### 4. Error Handling
- [ ] Login with wrong password shows error
- [ ] API failures show user-friendly messages
- [ ] Loading spinners display during fetches
- [ ] Network errors handled gracefully

#### 5. Permissions
- [ ] Non-admin users can't access admin endpoints
- [ ] Project members see only their projects
- [ ] Task assignees can update their tasks
- [ ] Change order approvals require permission

---

## QUICK FIXES FOR COMMON ISSUES

### Issue: CORS Error
**Solution:** Verify Django settings has `http://localhost:3000` in CORS_ALLOWED_ORIGINS

### Issue: 401 Unauthorized
**Solution:** Check token in localStorage, try logging out and back in

### Issue: Widgets Show No Data
**Solution:** 
1. Check Network tab - is request successful?
2. Verify endpoint returns `{results: [...]}` or `[...]`
3. Check `data.results || data` fallback in code

### Issue: Token Expired
**Solution:** Should auto-refresh. If not, check refreshToken exists in localStorage

### Issue: Build Fails
**Solution:** 
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## PRODUCTION DEPLOYMENT (After Testing)

### Environment Variables

**`.env.development`**
```
REACT_APP_API_URL=http://localhost:8000/api/v1
```

**`.env.production`**
```
REACT_APP_API_URL=https://yourdomain.com/api/v1
```

### Django Production Settings

```python
# settings.py additions
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
    CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']
```

### Deployment Steps

```bash
# 1. Build frontend for production
cd frontend/navigation
npm run build

# 2. Collect static files
cd ../../
python3 manage.py collectstatic --noinput

# 3. Run migrations (if any)
python3 manage.py migrate

# 4. Create superuser (if not exists)
python3 manage.py createsuperuser

# 5. Test production build locally
python3 manage.py runserver --insecure

# 6. Deploy to server (Heroku/Render/AWS/etc.)
git push heroku main
```

---

## SUCCESS CRITERIA

Phase 5 is **100% COMPLETE** when:

1. ✅ Backend API running with 0 errors
2. ✅ All 27 backend tests passing
3. ✅ Frontend builds successfully
4. ✅ Login flow works end-to-end
5. ✅ All widgets fetch real data
6. ✅ Token refresh works automatically
7. ✅ No CORS errors
8. ✅ No console errors
9. ✅ CRUD operations functional
10. ✅ Permissions enforced

---

## ESTIMATED TIME TO COMPLETION

- **Frontend Updates:** 1-2 hours
- **Testing:** 30 minutes
- **Bug Fixes:** 30 minutes
- **Documentation:** 30 minutes

**Total:** 2.5-3.5 hours

---

## SUPPORT COMMANDS

```bash
# Check Django server status
curl http://localhost:8000/api/v1/docs/

# Test JWT authentication
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"testpass123"}'

# Test protected endpoint
curl http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Run tests
python3 manage.py test core.tests.api

# Build frontend
cd frontend/navigation && npm run build

# Check for errors
tail -f /tmp/django.log  # If logging configured
```

---

**Last Updated:** November 30, 2025  
**Status:** Backend Complete, Frontend 25% (Ready for final push!)
