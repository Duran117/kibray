# OWNER DECISION QUESTIONNAIRE
**Status: ✅ COMPLETED**  
**Date Completed: December 8, 2025**

---

## 1. PROJECT STATE & VISION

### 1.1 Current Phase
**ANSWER:** The system is in a restructuring, consolidation, and modernization stage.

### 1.2 Definition of "Done"
**ANSWER:** A fully unified, clean, intelligent, mobile-first, operational Command Center for Kibray Paint & Stain.

### 1.3 High-Level Goals
**ANSWER:** The entire system must operate as the Business Command Center for the company. Calendar, AI, financials, tasks, PM workflows, and client communication must function together seamlessly.

### 1.4 Milestones / Deadlines
**ANSWER:** Soft milestones. No strict deadlines. Prioritize quality, clarity, and correctness over speed.

---

## 2. FEATURE PRIORITIES

### Priority Levels

**HIGH PRIORITY:**
- AI Quick Mode
- Calendar / Schedule
- Financial Module
- Notifications
- Strategic Planner
- Wizards
- WebSocket/Real-time communication

**MEDIUM PRIORITY:**
- SOP System

**LOW / FUTURE:**
- External integrations beyond Apple/Google calendar

---

## 3. BUSINESS LOGIC CLARIFICATION

### 3.1 System Philosophy
**ANSWER:** Flexible system with strong guardrails.

### 3.2 Mandatory Behaviors
**ANSWER:** Intelligent, proactive AI assistance tracking risks, missing elements, conflicts, inconsistencies, and errors.

### 3.3 Optional Features
**ANSWER:** Integrations with external platforms (except Google/Apple calendar).

### 3.4 Must Preserve
**ANSWER:**
- Calendar System
- Financial Module
- AI Quick Mode
- Notifications
- Daily Plan + Strategic Planner
- Project Module
- Task/Assignment System
- Change Orders
- Proposals/Estimates

### 3.5 Can Be Rewritten
**ANSWER:** Anything that causes confusion or inefficiency. Code can be modernized aggressively.

---

## 4. ROLES & PERMISSIONS

### ADMIN
**Can SEE:** Everything in the entire system.  
**Can MODIFY:** Everything in the entire system.

### PM (Project Manager)
**Can SEE:**
- All operational data for their assigned projects
- If multiple PMs share a project → all assigned PMs have full access to that project

**Can MODIFY:**
- Everything inside their assigned projects (calendar, tasks, COs, materials, photos, progress)

**CANNOT MODIFY:**
- Global finances
- Other PM projects
- System settings
- Roles

### EMPLOYEE
**Can SEE:**
- Only their tasks, instructions, schedules, and SOPs related to their work

**Can MODIFY:**
- Only their own progress (mark tasks done, upload photos, log notes, report issues)

### CLIENT
**Can SEE:**
- Full project timeline (except internals)
- Estimate, COs, invoices
- Progress (photos, notes approved by admin)
- All events relevant to the project
- Project calendar (no internal team data)

**CANNOT SEE:**
- Internal finances, payroll, internal materials, PM notes, employee tasks, or other projects

**Can MODIFY:**
- Approve/reject COs
- Add comments, files, photos
- Comment on the calendar

**CANNOT:**
- Delete items (admin approval required)

---

## 5. CALENDAR / SCHEDULE SYSTEM

### 5.1 Architecture
**ANSWER:** Modular base calendar with layered visibility depending on role.

### 5.2 Required Views
**ANSWER:**
- Timeline (Gantt-style)
- Daily view
- Weekly view
- Monthly view
- Expandable task blocks
- AI insights layer

### 5.3 Interaction
**ANSWER:** Full drag & drop support for PMs & Admin.

### 5.4 AI Behavior
**ANSWER:** Active AI with recommendations and alerts. Detects conflicts, risks, missing tasks, illogical dates.

### 5.5 Integration
**ANSWER:** Full bidirectional sync with Apple Calendar and Google Calendar.

### 5.6 Client Calendar Rules
**ANSWER:** Can see almost everything except financial and internal team data.

---

## 6. DOCUMENTATION STRATEGY

### 6.1 What Gets Archived
**ANSWER:** Everything outdated, duplicated, or contradicting the new unified documentation.

### 6.2 Official Documentation
**ANSWER:** Only MASTER documents are official:
- ARCHITECTURE_UNIFIED.md
- REQUIREMENTS_OVERVIEW.md
- MODULES_SPECIFICATIONS.md
- ROLE_PERMISSIONS_REFERENCE.md
- API_ENDPOINTS_REFERENCE.md
- CALENDAR_COMPLETE_GUIDE.md
- SECURITY_COMPREHENSIVE.md
- DEPLOYMENT_MASTER.md
- PHASE_SUMMARY.md

### 6.3 Consolidation Strategy
**ANSWER:** Strict consolidation with zero duplication.

### 6.4 Language
**ANSWER:** All internal and client-facing documentation must be in English.

---

## 7. CODE CLEANUP RULES

### 7.1 Cleanup Level
**ANSWER:** Aggressive cleanup. Remove all unused or obsolete code.

### 7.2 Legacy Handling
**ANSWER:** Move all legacy modules to /legacy folder untouched. Create LEGACY_MANIFEST.md.

### 7.3 Untouchable Modules
**ANSWER:**
- Calendar
- Financials
- AI
- Notifications
- Project module
- Tasks
- CO system
- Estimates

### 7.4 Admin Classes
**ANSWER:** Remove all unused Admin Classes permanently.

### 7.5 Refactoring Rules
**ANSWER:** Aggressive refactor to modern standards. Change internal architecture freely but preserve business behavior.

---

## 8. DEPLOYMENT & ENVIRONMENT

### 8.1 Deployment Workflow
**ANSWER:** Push to main → auto-deploy to Railway.

### 8.2 Secrets Handling
**ANSWER:** All secrets stored ONLY in Railway environment variables.

### 8.3 Pre-Deployment Validation
**ANSWER:** Full validation suite:
- Unit tests
- Integration tests
- Permissions tests
- Financial tests
- Calendar tests
- Startup checks
- IA readiness
- Documentation integrity
- API health check
- Dashboard smoke test

---

## 9. FINANCIAL MODEL RULES

### 9.1 Visibility
**ANSWER:** Strict visibility by role (Admin sees all, PM only their projects, Employee none, Client invoices/CO only).

### 9.2 Metrics Required
**ANSWER:** Full profitability system:
- Ingresos, Gastos, Profit
- ROI
- Budget vs Actual
- Phase performance
- CO financial impact
- Forecasting

### 9.3 Display Style
**ANSWER:** Full breakdown with dynamic charts.

### 9.4 Automation
**ANSWER:** AI-assisted automation with human approval.

---

## 10. AI ASSISTANT EXPECTATIONS

### 10.1 When AI Intervenes
**ANSWER:** Proactively whenever it detects issues.

### 10.2 Autonomous Decisions
**ANSWER:** Only small operational decisions. Major decisions require approval.

### 10.3 AI Can Autogenerate
**ANSWER:**
- Reminders
- Follow-up tasks
- Checklists
- Minor internal tasks
- Operational support tasks

### 10.4 Tone & Behavior
**ANSWER:** Professional, Concise, Clear, Proactive, Non-emotional.

---

## 11. USER EXPERIENCE EXPECTATIONS

### 11.1 UI Style
**ANSWER:** Clean, minimal, essential-only. No clutter.

### 11.2 Dashboard
**ANSWER:** Operational dashboard as the main view. Metrics accessible only after clicking a button.

### 11.3 Mobile
**ANSWER:** Mobile-first experience for PMs and employees.

### 11.4 Accessibility
**ANSWER:** Standard accessibility: simple navigation, readable text, high contrast.

---

## 12. FINAL DIRECTIVE

### 12.1 Additional Decisions
**ANSWER:** No additional decisions required.

### 12.2 Authorization
**ANSWER:** Copilot is fully authorized to:
- Consolidate documentation
- Clean unused code
- Refactor aggressively
- Modernize architecture
- Restructure modules
- Implement all rules defined above
- Enforce all permissions
- Improve quality everywhere

**This document overrides all previous instructions.**

---

✅ **QUESTIONNAIRE COMPLETE — READY FOR EXECUTION**
