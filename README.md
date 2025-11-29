# 🎨 Kibray - Construction Management System

**Professional painting contractor management platform**

[![Python](https://img.shields.io/badge/Python-3.11.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2.8-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Tests-670%20passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-85%25-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-black-black.svg)](https://github.com/psf/black)
[![Linter](https://img.shields.io/badge/Linter-ruff-blue.svg)](https://github.com/astral-sh/ruff)
[![PWA](https://img.shields.io/badge/PWA-Enabled-purple.svg)](https://web.dev/progressive-web-apps/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](./00_MASTER_STATUS_NOV2025.md)

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Status](#system-status)
- [Features](#features)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Testing & Quality](#testing--quality)
- [Documentation](#documentation)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)

---

## 🎯 Overview

Kibray is a comprehensive construction management platform designed specifically for painting contractors. It streamlines project management, financial tracking, employee performance, and field operations.

**System Status**: ✅ **95% Complete - Production Ready**  
**Tests**: 670 passing | **API Endpoints**: 45+ ViewSets | **Modules**: 15+ implemented

**Key Capabilities:**
- 📊 Financial dashboards and reporting
- 👷 Employee performance tracking with bonus system
- 📱 Progressive Web App (installable on all devices)
- 🔍 Global search across all resources
- 📋 Change order management with Kanban board
- 🖼️ Digital floor plans with pin annotations
- 💬 Project-based chat system
- 📅 Daily planning and scheduling
- 🧾 Invoice and expense tracking
- 💰 Advanced payroll with tax compliance
- 📦 Inventory valuation (FIFO/LIFO/AVG)
- 🔐 Digital signatures and 2FA security

---

## 📊 System Status

> 🎉 **All Critical Gaps (A-F) Completed!**

For complete system status, see: **[`00_MASTER_STATUS_NOV2025.md`](./00_MASTER_STATUS_NOV2025.md)**

### Implementation Status
- ✅ **Gap A**: Digital Signatures (5 tests)
- ✅ **Gap B**: Advanced Payroll (8 tests)
- ✅ **Gap C**: Invoice Payment Workflows (5 tests)
- ✅ **Gap D**: Inventory Valuation Methods (12 tests)
- ✅ **Gap E**: Advanced Financial Reporting (5 tests)
- ✅ **Gap F**: Client Portal Enhancements (7 tests)

### Test Coverage
```
Total Tests:    670
Passing:        667 (99.6%)
Skipped:        3 (0.4%)
Failing:        0 ✅
```

### Key Metrics
- **API Endpoints**: 45+ ViewSets + 15+ custom endpoints
- **Database Models**: 79
- **URLs Registered**: 233
- **Migrations**: 93
- **Code Coverage**: 85%

---

## ✨ Features

### **Gaps A-F: Production-Ready Enhancements**

#### Gap A: Digital Signatures ✅
- Sign invoices, contracts, and change orders digitally
- Secure signature storage with SHA-256 hashing
- Audit trail for all signed documents
- API: `POST /api/v1/documents/{id}/sign/`

#### Gap B: Advanced Payroll ✅
- Automated payroll periods (weekly/biweekly/monthly)
- Tax calculations (federal, state, FICA)
- Individual tax profiles per worker
- Payment tracking with references
- API: `/api/v1/payroll/*`

#### Gap C: Invoice Payment Workflows ✅
- Multi-state invoice workflow (draft → pending → approved → paid)
- Role-based approval permissions
- State transition validation
- API: `/api/v1/invoices/{id}/approve/`, `/api/v1/invoices/{id}/mark_as_paid/`

#### Gap D: Inventory Valuation ✅
- FIFO, LIFO, and Average Cost methods
- Inventory aging analysis
- Cost of Goods Sold (COGS) calculations
- API: `/api/v1/inventory/valuation-report/`, `/api/v1/inventory/items/{id}/calculate_cogs/`

#### Gap E: Advanced Financial Reporting ✅
- Invoice aging report with buckets (0-30, 31-60, 61-90, 90+ days)
- 90-day cash flow projection
- Budget variance analysis by project
- API: `/api/v1/financial/aging-report/`, `/api/v1/financial/cash-flow-projection/`

#### Gap F: Client Portal Enhancements ✅
- Client invoice viewing with filtering
- Invoice approval workflow for clients
- Project-level access control
- API: `/api/v1/client/invoices/`, `/api/v1/client/invoices/{id}/approve/`

### **Financial Management**
- Executive dashboard with KPIs (Revenue, Expenses, Profit, AR, Cash Flow)
- Invoice aging reports (0-30, 31-60, 61-90, 90+ days)
- QuickBooks export (CSV)
- Budget tracking per project
- Expense categorization

### **Employee Performance & Bonuses**
- Auto-tracked annual metrics (productivity, attendance, quality)
- Manual performance ratings (1-5 stars)
- Overall score calculation (weighted formula)
- Bonus decision system with justification
- Certification tracking
- Skill level progression

### **Progressive Web App (PWA)**
- Installable on iOS, Android, Windows, Mac
- Offline functionality
- Auto-updates every hour
- Native app experience (fullscreen, no browser bar)
- 4 quick shortcuts (Dashboard, Projects, Planning, Financial)

### **Global Search**
- Universal search bar (Ctrl+K or Cmd+K)
- Searches: Projects, Change Orders, Invoices, Employees, Tasks
- Results in <200ms
- Autocomplete dropdown with organized results
- Debounced for performance (300ms)

### **Change Order Management**
- Kanban board with drag & drop
- Touch-friendly mobile interface
- Horizontal scroll on mobile
- Status tracking (Pending → Approved → Sent → Billed → Paid)
- Time entry and expense linking

### **Project Management**
- Digital floor plans with pin annotations
- Color sample galleries
- Damage reports
- Punch lists (QC final verification)
- Subcontractor assignments
- Material inventory tracking

### **Communication**
- Project-based chat channels
- Real-time notifications
- Email digests
- Task assignments

---

## 🆕 Recent Updates (v2.0.0 - January 2025)

### **Major Features Added:**

#### ✅ **Financial System (FASE 1)**
- 9 new models + 2 extended models
- 5 financial dashboards and reports
- Employee performance metrics with bonus system
- Subcontractor management
- Punch list digitalization
- Migration `0056` successfully applied

#### ✅ **Progressive Web App (FASE 2)**
- Complete PWA implementation
- Service worker with offline caching
- Install prompts for all platforms
- Auto-update mechanism
- Custom offline page

#### ✅ **Global Search (FASE 2)**
- API endpoint `/api/search/`
- Navbar search bar on all pages
- Keyboard shortcut (Ctrl+K)
- 5 entity types searchable

#### ✅ **Proposal Email Sending & Audit Logging**
- Internal PM interface to email proposal link to client
- HTML + plain-text email with secure public token link
- Recipient auto-prefill (project client or first client access user)
- Persistent logging model `ProposalEmailLog` capturing success/fail + preview
- 3 dedicated tests (send success, failure logging, modal partial load)
- Non-regression: existing public approval flow unaffected
- Performance optimized (<200ms)

#### 🟡 **Mobile Optimization (FASE 3 - In Progress)**
- Change Order board optimized (touch drag & drop)
- 4 more templates pending optimization
- Horizontal scroll Kanban
- Large touch targets (>44px)

#### ⏳ **Pending:**
- Push notifications (OneSignal integration)
- Complete mobile optimization (4/5 templates)
- PWA final icons generation

**Total:** 6,100+ lines of new code, 30+ files created/modified

---

## 🆕 FASE 2 (Nov 2025) – Module 11: Tasks Enhancements

Major improvements to the Tasks subsystem with end-to-end API support and tests.

Highlights:
- Priorities (low, medium, high, urgent) and optional due dates
- Task dependencies with circular/self-dependency validation
- Time tracking (start/stop) and aggregated hours via `total_hours`
- Versioned task images (auto-increment, is_current)
- Reopen mechanic with audit trail (`TaskStatusChange`) and `reopen_events_count`
- Touch-up Kanban board endpoint and Gantt data endpoint
- New API actions: `reopen`, `start_tracking`, `stop_tracking`, `time_summary`, `add_image`, `add_dependency`, `remove_dependency`

Docs: see API details in `API_README.md` → Tasks section.

Testing:
- 61 passing tests for Module 11 (priorities, dependencies, cycles, due dates, images, time tracking, reopen)
- Reopen audit trail fixed to avoid duplicate entries; counts now accurate

Notes:
- Module-level coverage for the exercised Task paths is green; overall file coverage for `core/models.py` is lower due to unrelated modules in the same file. Consider extracting Task-related code into a dedicated module to track focused coverage.

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- PostgreSQL 14+ (production) or SQLite (development)
- pip, virtualenv

### **Installation**

```bash
# Clone repository
git clone <repository-url>
cd kibray

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

---

## 💻 Development Setup

### **Environment Configuration**

Create a `.env` file (optional for development):
```bash
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
# For production: DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### **Running Tests**

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_signatures_api.py

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Quick test (recent security/performance tests only)
pytest tests/test_signatures_api.py tests/test_reports_api.py tests/test_performance_queries.py -q
```

**Current Test Status**: ✅ **481 passed**, 2 skipped, 0 failures

### **Code Quality Tools**

#### **Linting with Ruff**
```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Check with statistics
ruff check . --statistics
```

#### **Formatting with Black**
```bash
# Check formatting
black . --check

# Format all files
black .

# Format with exclusions (automatic)
black . --force-exclude 'core/consumers_fixed.py'
```

#### **Pre-commit Hook** (Optional)
```bash
# Install pre-commit hook
cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

This will automatically run ruff, black, and tests before each commit.

### **VS Code Tasks**

The project includes integrated tasks (`.vscode/tasks.json`):
- **Run signature smoke tests**: Quick test verification
- **Run tests with coverage**: Full coverage report
- **Lint with ruff**: Check code quality
- **Lint and fix with ruff**: Auto-fix issues
- **Format with black**: Format all code

Access via: `Cmd+Shift+P` → "Tasks: Run Task"

---

## 🧪 Testing & Quality

### **Test Structure**

```
tests/
├── test_signatures_api.py       # Digital signature verification tests
├── test_reports_api.py          # CSV report generation tests
├── test_performance_queries.py  # N+1 query regression tests
├── test_module*.py              # Feature module tests
└── e2e/                         # End-to-end tests
```

### **Coverage Reports**

Current coverage: **50%** (baseline established)  
Target: **>90%** for production readiness

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open report
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
# start htmlcov/index.html  # Windows
```

### **Continuous Integration**

GitHub Actions workflow automatically runs on push/PR:
- ✅ Runs full test suite
- ✅ Generates coverage report
- ✅ Uploads coverage artifact

Workflow file: `.github/workflows/ci.yml`

### **Performance Testing**

Query performance regression tests prevent N+1 patterns:

```python
# Example: Budget overview should use ≤5 queries
def test_project_budget_overview_query_count(api_client, user):
    with CaptureQueriesContext(connection) as ctx:
        response = api_client.get('/api/v1/projects/budget-overview/')
    assert len(ctx.captured_queries) <= 5
```

---
# Clone repository
git clone https://github.com/yourusername/kibray.git
cd kibray

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb kibray_db
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver
```

### **Access**
- **Web:** http://localhost:8000
- **Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api/

### **Install as PWA**
1. Open Kibray in Chrome/Safari
2. Look for "Install" icon in address bar
3. Click "Install" button
4. App opens in standalone window

---

## 📚 Documentation

### **Getting Started**
- **[Quick Start](QUICK_START.md)** - Fast setup guide
- **[Development Setup](#development-setup)** - Detailed environment configuration
- **[Testing & Quality](#testing--quality)** - Test execution and coverage

### **Feature Guides**
- **[PWA Setup Guide](PWA_SETUP_COMPLETE.md)** - Progressive Web App documentation
- **[Global Search Guide](GLOBAL_SEARCH_GUIDE.md)** - Search functionality manual
- **[Visual & Collaboration Guide](VISUAL_COLLAB_GUIDE.md)** - Site Photos, Color Samples, Floor Plans & Damage Reports
- **[Invoice Builder Guide](INVOICE_BUILDER_GUIDE.md)** - Invoice creation and management
- **[Gantt Setup Guide](GANTT_SETUP_GUIDE.md)** - Project scheduling

### **Technical Documentation**
- **[API Documentation](API_README.md)** - REST API reference
- **[Database Schema Audit](DB_SCHEMA_AUDIT.md)** - Model constraints and validation
- **[System Analysis](SYSTEM_ANALYSIS.md)** - Full system breakdown
- **[Financial Module Analysis](FINANCIAL_MODULE_ANALYSIS.md)** - Financial system architecture

### **Quality & Maintenance**
- **[MCP Server Troubleshooting](MCP_SERVER_TROUBLESHOOTING.md)** - Pylance MCP configuration
- **[Optimization Report](OPTIMIZATION_REPORT.md)** - Performance improvements
- **[Implementation Status Audit](IMPLEMENTATION_STATUS_AUDIT.md)** - Feature completion tracker

---

## 🛠️ Tech Stack

### **Backend**
- **Framework:** Django 5.2.4
- **Database:** PostgreSQL 14 (production), SQLite (development)
- **API:** Django REST Framework 3.15.2
- **Auth:** JWT (simplejwt), 2FA TOTP (custom implementation)
- **Tasks:** Celery (async processing)
- **Storage:** AWS S3 (production)

### **Testing & Quality**
- **Testing:** pytest 8.3.3, pytest-django 4.9.0, pytest-cov 5.0.0
- **Linter:** ruff 0.8.4 (pycodestyle, pyflakes, isort, bugbear)
- **Formatter:** black 24.10.0 (line-length 120)
- **CI/CD:** GitHub Actions

### **Frontend**
- **UI:** Bootstrap 5.3.3
- **Icons:** Bootstrap Icons 1.11.3
- **Charts:** Chart.js 4.4.0
- **Maps:** Leaflet.js (floor plans)
- **PWA:** Workbox (service worker)

### **Mobile**
- **PWA:** Manifest + Service Worker
- **Touch:** Native drag & drop API
- **Responsive:** Mobile-first design

### **DevOps**
- **Deployment:** Render.com
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry (optional)

---

## 📁 Project Structure

```
kibray/
├── core/                          # Main Django app
│   ├── models.py                  # 25+ models (Project, Invoice, etc.)
│   ├── views.py                   # Main views
│   ├── views_financial.py         # ✨ NEW: Financial dashboards (5 views)
│   ├── admin.py                   # Admin panels (20+)
│   ├── api/
│   │   ├── views.py               # ✨ NEW: global_search API
│   │   ├── serializers.py         # DRF serializers
│   │   └── urls.py                # API routes
│   ├── templates/
│   │   └── core/
│   │       ├── base.html          # ✨ UPDATED: PWA + Search
│   │       ├── financial_dashboard.html          # ✨ NEW
│   │       ├── invoice_aging_report.html         # ✨ NEW
│   │       ├── productivity_dashboard.html       # ✨ NEW
│   │       ├── employee_performance_list.html    # ✨ NEW
│   │       ├── employee_performance_detail.html  # ✨ NEW
│   │       ├── changeorder_board.html   # ✨ OPTIMIZED: Mobile
│   │       ├── offline.html             # ✨ NEW: PWA offline page
│   │       └── partials/
│   │           └── _co_card.html        # ✨ NEW: CO card component
│   ├── static/
│   │   ├── manifest.json          # ✨ NEW: PWA manifest
│   │   ├── service-worker.js      # ✨ NEW: PWA service worker
│   │   └── icons/
│   │       ├── icon.svg           # ✨ NEW: Base icon
│   │       └── generate-icons.html # ✨ NEW: Icon generator
│   ├── migrations/
│   │   └── 0056_*.py              # ✨ NEW: 9 models + 2 extended
│   └── tests/
├── kibray_backend/                # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── frontend/                      # Vite frontend (if applicable)
├── locale/                        # i18n translations (en, es)
├── scripts/                       # Deployment scripts
├── requirements.txt               # Python dependencies
├── manage.py                      # Django management
├── PWA_SETUP_COMPLETE.md          # ✨ NEW: PWA documentation
├── GLOBAL_SEARCH_GUIDE.md         # ✨ NEW: Search documentation
├── MOBILE_OPTIMIZATION_STATUS.md  # ✨ NEW: Mobile progress
├── IMPLEMENTATION_SUMMARY.md      # ✨ NEW: Full changelog
└── README.md                      # This file
```

---

## 🔑 Key Models

### **Core Business**
- **Project** - Construction projects
- **ChangeOrder** - Project modifications
- **Invoice** - Customer invoicing
- **Expense** - Project expenses
- **TimeEntry** - Employee time tracking

### **New Financial (v2.0)**
- **EmployeePerformanceMetric** ✨ - Annual performance for bonuses
- **Subcontractor** ✨ - Subcontractor management
- **SubcontractorAssignment** ✨ - Project assignments
- **PunchListItem** ✨ - QC punch lists
- **EmployeeCertification** ✨ - Employee certs
- **EmployeeSkillLevel** ✨ - Skill progression
- **SOPCompletion** ✨ - SOP tracking

### **Collaboration**
- **ChatChannel** - Project chat rooms
- **ChatMessage** - Messages
- **Task** - Task management
- **Notification** - User notifications

### **Planning**
- **FloorPlan** - Digital floor plans
- **PlanPin** - Annotations on plans
- **ColorSample** - Color palettes
- **DamageReport** - Damage documentation

---

## 🌐 API Endpoints

### **Authentication**
```
POST /api/auth/login/          # JWT token obtain
POST /api/auth/refresh/        # JWT token refresh
```

### **Search** ✨ NEW
```
GET  /api/search/?q=query      # Global search
```

### **Projects**
```
GET    /api/projects/          # List projects
GET    /api/projects/:id/      # Project detail
POST   /api/projects/          # Create project
PATCH  /api/projects/:id/      # Update project
DELETE /api/projects/:id/      # Delete project
```

### **Change Orders**
```
GET    /api/changeorders/      # List COs
GET    /api/changeorders/:id/  # CO detail
PATCH  /api/changeorders/:id/update-status/  # Update status (drag&drop)
```

### **Tasks**
```
GET    /api/tasks/             # List tasks
POST   /api/tasks/             # Create task
PATCH  /api/tasks/:id/         # Update task
```

### **Notifications**
```
GET    /api/notifications/     # List notifications
POST   /api/notifications/mark-all-read/  # Mark all read
GET    /api/notifications/count-unread/   # Unread count
```

*Full API documentation: [API_README.md](API_README.md)*

---

## 📱 PWA Features

### **Installability**
- ✅ Manifest configured
- ✅ Service worker registered
- ✅ Install prompts on all platforms
- ✅ 192x192 and 512x512 icons
- ✅ Start URL: `/dashboard/`

### **Offline Support**
- ✅ Cached pages (Dashboard, Projects, etc.)
- ✅ Cached assets (CSS, JS, images)
- ✅ Custom offline page
- ✅ Network-first strategy for dynamic content

### **Updates**
- ✅ Auto-check every hour
- ✅ User prompt for new versions
- ✅ Skip waiting implementation
- ✅ Reload after update

### **Shortcuts**
1. Dashboard (`/dashboard/`)
2. Projects (`/projects/`)
3. Daily Planning (`/daily-planning/`)
4. Financial (`/financial/dashboard/`)

*Complete guide: [PWA_SETUP_COMPLETE.md](PWA_SETUP_COMPLETE.md)*

---

## 🔍 Global Search Usage

### **Keyboard Shortcut**
```
Ctrl+K  (Windows/Linux)
Cmd+K   (macOS)
```

### **What's Searchable**
- Projects (name, address, client)
- Change Orders (number, description)
- Invoices (number, client)
- Employees (name, email, phone, position)
- Tasks (title, description)

### **Example Searches**
```
Johnson Residence     → Projects named "Johnson"
CO-2024-015          → Change Order #2024-015
INV-1523             → Invoice #1523
john@example.com     → Employee with email
555-1234             → Employee with phone
```

*Full documentation: [GLOBAL_SEARCH_GUIDE.md](GLOBAL_SEARCH_GUIDE.md)*

---

## 🎯 Performance

### **Metrics**
- Lighthouse PWA Score: **95+**
- Search response time: **<200ms**
- Dashboard load time: **<1s**
- Mobile scroll: **60 FPS**

### **Optimization**
- Database queries optimized with `select_related()`
- Static files cached (1 year)
- Service worker caching
- Debounced search (300ms)
- Lazy loading images

---

## 🧪 Testing

### **Run Tests**
```bash
# All tests
pytest

# Specific app
pytest core/tests/

# Coverage
pytest --cov=core
```

### **Test PWA**
1. Open DevTools (F12)
2. Go to **Application** tab
3. Check **Service Workers** (should show active)
4. Check **Manifest** (should show Kibray)
5. Run **Lighthouse** audit (should score 90+)

### **Test Search**
1. Press `Ctrl+K`
2. Type "test"
3. Should see results in <300ms
4. Press `Esc` to close

---

## 🚢 Deployment

### **Render.com (Production)**
```bash
# Automatic deployment on push to main
git push origin main

# Manual deploy
render deploy
```

### **Environment Variables**
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/dbname
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### **Post-Deployment**
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # if first deploy
```

---

## 👥 Contributing

### **Development Workflow**
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### **Code Style**
- Python: PEP 8
- JavaScript: ESLint
- HTML/CSS: Prettier
- Max line length: 120 characters

### **Commit Messages**
```
feat: Add global search functionality
fix: Correct PWA manifest path
docs: Update README with PWA instructions
style: Format code with black
refactor: Simplify search query logic
test: Add tests for financial dashboard
```

---

## 📄 License

**Proprietary** - All rights reserved. This software is for internal use only.

---

## 🙏 Acknowledgments

- Django community for excellent documentation
- Bootstrap team for responsive UI framework
- Chart.js for beautiful charts
- Workbox for PWA tooling

---

## 📞 Support

**Documentation:** See `docs/` folder for detailed guides

**Issues:** Contact development team

**Updates:** Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for latest changes

---

## 🗺️ Roadmap

### **Q1 2025**
- [x] Financial dashboard system
- [x] Employee performance tracking
- [x] PWA implementation
- [x] Global search
- [ ] Complete mobile optimization (80% done)
- [ ] Push notifications (OneSignal)

### **Q2 2025**
- [ ] AI defect detection (site photos)
- [ ] Voice commands
- [ ] Advanced analytics
- [ ] Mobile app (React Native)

### **Q3 2025**
- [ ] Client portal
- [ ] Automated scheduling
- [ ] Inventory QR codes
- [ ] Integration with accounting systems

---

## 📊 Statistics

- **Total Code:** 20,000+ lines
- **Models:** 25+
- **Views:** 50+
- **Templates:** 60+
- **API Endpoints:** 30+
- **Migrations:** 56
- **Tests:** 100+
- **Documentation:** 2,000+ lines

---

**Built with ❤️ for painting contractors**

**Version:** 2.0.0  
**Last Updated:** January 13, 2025
