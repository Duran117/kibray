# REQUIREMENTS OVERVIEW
**System:** Kibray ERP - Business Command Center  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## SYSTEM VISION

Kibray ERP is a **fully unified, clean, intelligent, mobile-first operational Command Center** for Kibray Paint & Stain. The system integrates all business operations into a seamless platform combining calendar management, AI assistance, financial tracking, project management, and client communication.

### Core Philosophy
- Flexible system with strong guardrails
- Intelligent, proactive AI assistance
- Mobile-first experience for PMs and employees
- Clean, minimal, essential-only UI

---

## HIGH-LEVEL SYSTEM GOALS

1. **Unified Operations:** All modules function together seamlessly
2. **Intelligent Assistance:** Proactive AI tracking risks, conflicts, and missing elements
3. **Role-Based Access:** Strict permissions per user role
4. **Real-Time Communication:** WebSocket-powered live updates
5. **Financial Transparency:** Complete profitability and budget tracking
6. **Client Visibility:** Project access without exposing internal operations

---

## MODULE PRIORITIES

### HIGH PRIORITY
1. **AI Quick Mode** - Intelligent assistant for rapid decisions
2. **Calendar/Schedule System** - Core operational calendar
3. **Financial Module** - Profitability, budgets, invoices
4. **Notifications** - Multi-channel notification system
5. **Strategic Planner** - Long-term planning and forecasting
6. **Wizards** - Guided workflows for complex operations
7. **WebSocket/Real-time** - Live data synchronization

### MEDIUM PRIORITY
8. **SOP System** - Standard Operating Procedures management

### LOW/FUTURE PRIORITY
9. **External Integrations** - Beyond Apple/Google Calendar

---

## MODULE 1: PROJECT MANAGEMENT

### Purpose
Central hub for managing all construction projects from creation to completion.

### Key Features

#### 1.1 Project Creation
**Flow 1 - From Proposal:**
- Proposal created → Client approves estimate → Auto-create project
- Inherits: Client, budget, estimate information
- Initial status: `created`

**Flow 2 - Direct Creation:**
- For touch-ups, T&M work, or projects without prior estimate
- Admin creates directly with minimal information

**Required Fields:**
- Client information (name, contact)
- Project location (full address)
- Basic project notes

**Optional Fields:**
- Initial budget
- Estimated dates
- Estimate link

#### 1.2 Project States
- `created` - Newly created project
- `active` - Auto-activates when first schedule item created
- `closed` - Project completed

#### 1.3 Project Dashboard
- Overview of all active projects
- Progress visualization
- Budget vs actual tracking
- Timeline view
- Risk alerts from AI

#### 1.4 Multi-PM Projects
- Multiple PMs can be assigned to one project
- All assigned PMs have full access to project data
- Changes visible to all PMs in real-time

#### 1.5 Project Archives
- Closed projects moved to archive
- Full history preserved
- Searchable and retrievable

### Validations
- Unique project names
- End date must be after start date
- Client must exist in system

---

## MODULE 2: CLIENT MANAGEMENT

### Purpose
Maintain client relationships and provide client portal access.

### Key Features

#### 2.1 Client Records
- Contact information
- Project history
- Communication logs
- Document storage
- Billing information

#### 2.2 Client Portal
**Can See:**
- Full project timeline (except internal notes)
- Estimates, change orders, invoices
- Progress photos and notes (admin-approved only)
- All events relevant to their project
- Project calendar (no internal team data)

**Can NOT See:**
- Internal finances
- Payroll data
- Internal materials costs
- PM notes
- Employee tasks
- Other projects

**Can Do:**
- Approve/reject change orders
- Add comments, files, photos
- Comment on calendar events
- Request updates

**Can NOT Do:**
- Delete items (requires admin approval)
- Modify schedules
- Access financial internals

#### 2.3 Client Communication
- Email integration
- SMS notifications
- In-app messaging
- Document sharing
- Approval workflows

---

## MODULE 3: SCHEDULE & CALENDAR SYSTEM

### Purpose
Modular calendar system with layered role-based visibility.

### Architecture
- **Base Calendar:** Core scheduling engine
- **Role Layers:** Different views per role
- **AI Layer:** Intelligent recommendations and alerts
- **Integration Layer:** Apple Calendar + Google Calendar bidirectional sync

### Required Views
1. **Timeline View** (Gantt-style)
   - Visual project timeline
   - Dependencies
   - Critical path
   - Resource allocation

2. **Daily View**
   - Today's tasks and events
   - Employee assignments
   - Priorities
   - Blockers

3. **Weekly View**
   - Week-at-a-glance
   - Resource planning
   - Conflict detection

4. **Monthly View**
   - High-level overview
   - Milestone tracking
   - Capacity planning

5. **Expandable Task Blocks**
   - Click to expand full details
   - Inline editing
   - Quick actions

6. **AI Insights Layer**
   - Risk indicators
   - Conflict warnings
   - Optimization suggestions
   - Missing task alerts

### Interaction
- **Drag & Drop:** Full support for PM and Admin
- **Inline Editing:** Quick updates without modal dialogs
- **Bulk Operations:** Multi-select for batch actions
- **Filtering:** By project, PM, employee, status
- **Search:** Full-text search across calendar

### AI Behavior
- **Proactive Detection:**
  - Schedule conflicts
  - Resource over-allocation
  - Illogical dates
  - Missing dependencies
  - Weather risks
  - Budget constraints

- **Recommendations:**
  - Optimal task ordering
  - Resource reallocation
  - Timeline adjustments
  - Risk mitigation

### External Integrations
- **Apple Calendar:** Full bidirectional sync
- **Google Calendar:** Full bidirectional sync
- **Sync Conflict Resolution:** AI-assisted merge

### Client Calendar View
- Almost full project visibility
- Excludes financial data
- Excludes internal team assignments
- Shows milestones and major events
- Shows progress updates

---

## MODULE 4: TASK & ASSIGNMENT SYSTEM

### Purpose
Granular task management and employee assignment tracking.

### Key Features

#### 4.1 Task Creation
- Manual creation by PM
- Auto-generation from templates
- AI-suggested tasks
- Recurring task patterns

#### 4.2 Task Properties
- Title, description, notes
- Assigned employees (single or multiple)
- Start/end dates
- Estimated hours
- Actual hours
- Priority level
- Status
- Dependencies
- Linked project
- Linked change order
- Photos/attachments

#### 4.3 Task States
- `pending` - Not yet started
- `in_progress` - Currently being worked
- `blocked` - Waiting on dependency or issue
- `completed` - Finished
- `cancelled` - No longer needed

#### 4.4 Employee Task View
- Mobile-optimized
- Only assigned tasks visible
- Mark progress
- Upload photos
- Log notes
- Report issues/blockers
- Track time

#### 4.5 PM Task Management
- Overview of all project tasks
- Reassign on the fly
- Modify dates via drag-drop
- Bulk operations
- Progress tracking
- Time tracking analysis

#### 4.6 Pin Cleanup Automation
- When task marked complete → associated pins auto-hidden
- Keeps floor plans clean
- Prevents clutter
- Maintains history

---

## MODULE 5: FINANCIAL SYSTEM

### Purpose
Complete financial management with strict role-based visibility.

### Architecture
Full profitability tracking system with AI-assisted automation requiring human approval for major decisions.

### Key Metrics

#### 5.1 Core Metrics
- **Ingresos (Income):** All revenue sources
- **Gastos (Expenses):** All costs
- **Profit:** Income - Expenses
- **ROI:** Return on investment percentage
- **Budget vs Actual:** Real-time variance tracking
- **Phase Performance:** Profitability by project phase
- **CO Financial Impact:** Change order effect on budget
- **Forecasting:** Predictive financial projections

#### 5.2 Visibility Rules

**Admin:**
- All financial data across entire system
- All projects, all metrics
- Full editing capability

**PM:**
- Only their assigned projects
- Project budget and actuals
- Phase performance
- Cannot see payroll
- Cannot see other projects

**Employee:**
- No financial access
- Can log time only

**Client:**
- Invoices only
- Change orders with prices
- No internal costs
- No profit margins
- No employee wages

### Features

#### 5.3 Invoicing System
- **Invoice Types:**
  - `standard` - Regular progress billing
  - `deposit` - Advance payment before work starts
  - `final` - Project completion with balance

- **Retention Amount:** Holdback for warranty/guarantee
- **Draft for Review:** PM Trainee invoices require admin approval
- **Auto-calculation:** Net payable after retention
- **Payment Tracking:** Paid/unpaid status

#### 5.4 Budgeting
- Initial project budget
- Phase-level budgets
- Real-time actuals tracking
- Variance alerts
- Forecast to completion

#### 5.5 Expense Tracking
- Material costs
- Labor costs
- Equipment costs
- Subcontractor costs
- Overhead allocation

#### 5.6 Employee Reimbursements
- 5-state tracking system:
  - `submitted` - Employee submitted claim
  - `under_review` - Admin reviewing
  - `approved` - Approved for payment
  - `paid` - Payment issued
  - `rejected` - Claim denied
- Photo/receipt attachments
- Approval workflow
- Payment history

#### 5.7 Profitability Analysis
- Project-level P&L
- Phase-level margins
- Historical trends
- Forecast modeling
- Benchmark comparisons

### Display Style
- Full breakdown with dynamic charts
- Clean, minimal interface
- Drill-down capability
- Export functionality
- Mobile-optimized views

---

## MODULE 6: CHANGE ORDERS

### Purpose
Track scope changes and their financial impact.

### Key Features

#### 6.1 Change Order Creation
- Linked to project
- Description of change
- Reason/justification
- Cost breakdown
- Timeline impact

#### 6.2 Approval Workflow
- PM creates change order
- Client reviews via portal
- Client approves/rejects
- Admin can override
- Auto-updates project budget upon approval

#### 6.3 Photo Annotations
- Visual documentation of changes
- Color-coded pins
- Before/after photos
- Measurements and notes

#### 6.4 Financial Impact
- Cost increase/decrease
- Budget reallocation
- Timeline adjustment
- Profit impact analysis

---

## MODULE 7: ESTIMATES & PROPOSALS

### Purpose
Create professional estimates and convert to projects.

### Key Features

#### 7.1 Estimate Creation
- Template-based or custom
- Line item breakdown
- Material costs
- Labor estimates
- Markup/margin
- Terms and conditions

#### 7.2 Client Presentation
- Professional PDF generation
- Online review portal
- Line-by-line pricing
- Optional items
- Payment terms

#### 7.3 Approval & Conversion
- Client approves estimate
- Auto-convert to project
- Budget established
- Schedule initialized

---

## MODULE 8: INVENTORY MANAGEMENT

### Purpose
Track materials, tools, and equipment.

### Key Features

#### 8.1 Inventory Tracking
- Item catalog
- Quantity on hand
- Location tracking
- Reorder points
- Cost tracking

#### 8.2 Bulk Transfer
- Transfer multiple items between projects
- Exclude surplus items
- Update project costs
- Maintain audit trail

#### 8.3 Material Requests
- Employee requests materials
- PM approves/denies
- Auto-updates inventory
- Tracks project allocation

---

## MODULE 9: STRATEGIC PLANNER

### Purpose
Intelligent long-term planning and resource optimization.

### Key Features

#### 9.1 Planning Tools
- Schedule weight calculation
- Progress percentage tracking
- Checklist generation
- Milestone planning

#### 9.2 AI Assistance
- Resource optimization
- Timeline predictions
- Risk forecasting
- Bottleneck identification

#### 9.3 Scenario Planning
- What-if analysis
- Resource reallocation
- Timeline adjustments
- Cost impact modeling

---

## MODULE 10: AI QUICK MODE

### Purpose
Intelligent assistant for rapid decisions and proactive monitoring.

### AI Behavior

#### 10.1 When AI Intervenes
- Detects issues proactively
- Alerts before problems escalate
- Suggests solutions
- Auto-generates minor tasks

#### 10.2 Autonomous Decisions
- Small operational decisions only
- Examples:
  - Reminder generation
  - Follow-up task creation
  - Checklist generation
  - Minor internal tasks
  - Operational support tasks

#### 10.3 Approval Required
- Major decisions require human approval:
  - Budget changes
  - Schedule modifications
  - Resource reallocation
  - Client communications

#### 10.4 Tone & Behavior
- Professional
- Concise
- Clear
- Proactive
- Non-emotional

#### 10.5 Detection Systems
**AI must detect and alert:**
- Risks (weather, supply chain, resource)
- Missing elements (tasks, documents, approvals)
- Conflicts (schedule, resource, priority)
- Inconsistencies (data, logic, workflow)
- Errors (calculation, entry, validation)

---

## MODULE 11: NOTIFICATIONS SYSTEM

### Purpose
Multi-channel notification delivery system.

### Notification Channels
1. **In-App:** Real-time browser notifications
2. **Email:** Formatted email alerts
3. **SMS:** Critical alerts via text
4. **Push:** Mobile app notifications (when implemented)

### Notification Types
- **Task Assigned:** Employee receives new task
- **Task Due Soon:** Reminder before deadline
- **Task Overdue:** Alert after missed deadline
- **Change Order:** Client approval needed
- **Invoice:** Payment reminder
- **Schedule Change:** Calendar update
- **Budget Alert:** Approaching or exceeding budget
- **Risk Alert:** AI-detected issue

### User Preferences
- Choose channels per notification type
- Quiet hours configuration
- Digest vs immediate delivery
- Notification grouping

---

## MODULE 12: WEBSOCKET & REAL-TIME

### Purpose
Live data synchronization across all connected clients.

### Features
- Real-time calendar updates
- Live task status changes
- Instant chat/messaging
- Collaborative editing indicators
- Presence detection
- Connection state management
- Auto-reconnect on failure

---

## MODULE 13: SOP SYSTEM (MEDIUM PRIORITY)

### Purpose
Standard Operating Procedures documentation and distribution.

### Features
- SOP creation wizard
- Template library
- Version control
- Employee acknowledgment tracking
- Search and retrieval
- Mobile access

---

## MODULE 14: COLOR SAMPLES & MATERIALS

### Purpose
Track color selections and material approvals.

### Key Features

#### 14.1 Color Sample Management
- Photo documentation
- Client approval workflow
- Integration with projects via approved_finishes JSON field
- Signature capture for approvals
- Before/after comparisons

#### 14.2 Material Specifications
- Product details
- Supplier information
- Cost tracking
- Quantity calculations
- Order history

---

## MODULE 15: VISUAL COLLABORATION

### Purpose
Floor plans, pins, and visual project communication.

### Key Features

#### 15.1 Floor Plan Pins
- Photo annotations
- Color-coded categories
- Task linkage
- Auto-hide on completion
- Measurement tools

#### 15.2 Photo Management
- Before/after documentation
- Client-facing galleries
- Internal-only photos
- Bulk upload
- Metadata tagging

---

## ROLE-BASED PERMISSIONS

### ADMIN
**Can See:** Everything in the entire system  
**Can Modify:** Everything in the entire system  
**Special:** Full system administration, user management, role assignment

### PROJECT MANAGER (PM)
**Can See:**
- All operational data for assigned projects
- Shared projects (multiple PMs have full access)
- Calendar, tasks, change orders, materials, photos, progress

**Can Modify:**
- Everything inside assigned projects
- Calendar, tasks, COs, materials, photos, progress

**Can NOT:**
- Modify global finances
- Access other PM projects
- Change system settings
- Modify roles

### EMPLOYEE
**Can See:**
- Only their assigned tasks
- Instructions and SOPs
- Schedules relevant to their work

**Can Modify:**
- Their own progress (mark tasks done)
- Upload photos and attachments
- Log notes and comments
- Report issues and blockers

**Can NOT:**
- Access other employees' data
- View financials
- Modify projects or schedules
- Access other projects

### CLIENT
**Can See:**
- Full project timeline (except internal notes)
- Estimates, change orders, invoices
- Progress (photos/notes approved by admin)
- All events relevant to project
- Project calendar (no internal team data)

**Can NOT See:**
- Internal finances, payroll, materials costs
- PM notes
- Employee tasks
- Other projects

**Can Modify:**
- Approve/reject change orders
- Add comments, files, photos
- Comment on calendar

**Can NOT:**
- Delete items (admin approval required)
- Modify schedules or budgets
- Access internal operations

---

## VALIDATION & BUSINESS RULES

### Project Validation
- Unique project names
- End date > Start date
- Client must exist
- PM must be assigned before project becomes active

### Financial Validation
- Invoice total = sum of line items
- Retention amount ≤ invoice total
- Payment amount ≤ invoice total - paid to date
- Budget changes require approval

### Schedule Validation
- No overlapping employee assignments
- Task end date ≥ task start date
- Dependencies must be valid tasks
- Cannot delete tasks with dependencies

### Permission Validation
- All API endpoints check permissions
- Frontend hides unauthorized UI elements
- Database queries filtered by role
- Audit logging for all modifications

---

## DEPLOYMENT & ENVIRONMENT

### Deployment Workflow
**Process:** Push to main → auto-deploy to Railway

### Secrets Management
- All secrets stored ONLY in Railway environment variables
- No secrets in codebase
- No secrets in version control

### Pre-Deployment Validation
**Required checks before deploy:**
1. Unit tests - all pass
2. Integration tests - all pass
3. Permissions tests - all roles validated
4. Financial tests - calculations verified
5. Calendar tests - sync, conflicts, views
6. Startup checks - migrations, static files
7. AI readiness - models loaded, APIs connected
8. Documentation integrity - links valid, content current
9. API health check - all endpoints responding
10. Dashboard smoke test - all views loading

---

## USER EXPERIENCE STANDARDS

### UI/UX Principles
- **Clean & Minimal:** Essential-only, no clutter
- **Mobile-First:** Optimized for PMs and employees on mobile
- **Accessibility:** Simple navigation, readable text, high contrast
- **Role-Appropriate:** Dashboard adapts to user role

### Dashboard Design
- **Main View:** Operational dashboard (tasks, calendar, alerts)
- **Metrics Access:** Behind button click to reduce clutter
- **Contextual:** Displays relevant info per role

### Mobile Experience
- **PM:** Full operational capability on mobile
- **Employee:** Task management, time tracking, photo upload
- **Client:** Project visibility and approvals

---

## SYSTEM INTEGRATIONS

### External Calendars
- **Apple Calendar:** Full bidirectional sync
- **Google Calendar:** Full bidirectional sync
- **Conflict Resolution:** AI-assisted merge strategy

### Future Integrations (Low Priority)
- Accounting systems
- Third-party scheduling tools
- Supply chain platforms
- Payment processors

---

## TESTING & QUALITY ASSURANCE

### Test Coverage Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- Permission tests for all roles
- Financial calculation tests
- Calendar sync tests
- UI smoke tests

### Continuous Testing
- Automated test execution on commit
- Pre-deployment test gate
- Post-deployment validation
- Performance monitoring

---

## DOCUMENTATION STANDARDS

### Documentation Principles
- All documentation in English only
- No duplication across documents
- Cross-reference appropriately
- Keep current with code changes
- Include examples and diagrams

### Master Documents
This document is one of 9 official master documents:
1. **ARCHITECTURE_UNIFIED.md** - System architecture
2. **REQUIREMENTS_OVERVIEW.md** (this document) - System requirements
3. **MODULES_SPECIFICATIONS.md** - Detailed module specs
4. **ROLE_PERMISSIONS_REFERENCE.md** - Permission matrix
5. **API_ENDPOINTS_REFERENCE.md** - API documentation
6. **CALENDAR_COMPLETE_GUIDE.md** - Calendar system guide
7. **SECURITY_COMPREHENSIVE.md** - Security documentation
8. **DEPLOYMENT_MASTER.md** - Deployment procedures
9. **PHASE_SUMMARY.md** - Implementation phase history

---

## CHANGE MANAGEMENT

### Code Changes
- Aggressive refactoring permitted
- Modernize freely
- Preserve business behavior exactly
- Update tests accordingly
- Update documentation

### Legacy Code
- Move to `/legacy/` folder
- Create LEGACY_MANIFEST.md
- Do not modify legacy code
- Reference in documentation if needed

### Cleanup Rules
- Remove all unused code aggressively
- Remove all unused admin classes permanently
- Document all functions
- Modernize to current standards

---

## CONCLUSION

This requirements document serves as the authoritative source for system functionality and business rules. All implementation must align with these requirements. Any deviations must be documented and approved by the system owner.

**Next Steps:**
- Refer to MODULES_SPECIFICATIONS.md for detailed technical specifications
- Refer to ROLE_PERMISSIONS_REFERENCE.md for permission matrix
- Refer to API_ENDPOINTS_REFERENCE.md for API details

---

**Document Control:**
- Version: 2.0
- Status: Official Master Document
- Owner Approved: December 8, 2025
- Previous Version: REQUIREMENTS_DOCUMENTATION.md (19,293 lines) - Archived
