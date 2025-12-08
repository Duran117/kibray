# ROLE PERMISSIONS REFERENCE
**System:** Kibray ERP  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## OVERVIEW

This document defines the complete permission matrix for all roles in the Kibray ERP system. Permissions are enforced at multiple levels:
1. **API Level:** Permission decorators on endpoints
2. **Frontend Level:** UI element visibility
3. **Database Level:** Query filtering by role
4. **Audit Level:** All actions logged with user/role

---

## ROLE HIERARCHY

```
┌─────────────────┐
│  ADMIN (Owner)  │  ← Full system access
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬─────────┐
    │          │          │         │
┌───▼────┐ ┌──▼────┐ ┌───▼────┐ ┌──▼──────┐
│   PM   │ │Designer│ │  Super │ │Employee │
│  Full  │ └────────┘ └────────┘ └─────────┘
└───┬────┘
    │
┌───▼────────┐
│ PM Trainee │
└────────────┘

    ┌──────────┐
    │  CLIENT  │  ← External access
    └──────────┘
```

---

## ROLE DEFINITIONS

### 1. ADMIN (General Manager / Owner)

**Role Code:** `admin` / `general_manager`  
**Permission Count:** 65 permissions  
**Custom Permissions:** `can_send_external_emails`

#### Can See:
✅ Everything in the entire system  
✅ All projects (all PMs)  
✅ All financial data  
✅ All employee data  
✅ All client data  
✅ System settings  
✅ Audit logs  
✅ Analytics and reports

#### Can Modify:
✅ Everything in the entire system  
✅ Create/edit/delete projects  
✅ Create/edit/delete users  
✅ Assign/change roles  
✅ Modify system settings  
✅ Override any restriction  
✅ Approve/reject everything  
✅ Financial transactions

#### Special Privileges:
- Full database access
- User management
- Role assignment
- System configuration
- Backup/restore operations
- API key management
- Override client restrictions
- Access archived data

---

### 2. PROJECT MANAGER (FULL)

**Role Code:** `project_manager_full`  
**Permission Count:** 51 permissions  
**Custom Permissions:** `can_send_external_emails`

#### Can See:
✅ All operational data for **assigned projects only**  
✅ If multiple PMs assigned to one project → all PMs have full access  
✅ Calendar for assigned projects  
✅ Tasks for assigned projects  
✅ Change orders for assigned projects  
✅ Materials for assigned projects  
✅ Photos/progress for assigned projects  
✅ Client communication for assigned projects  
✅ Project financial data (budgets, invoices)

❌ **Cannot See:**
- Other PM projects
- Global financial reports
- Payroll data
- System settings
- Other employees' personal data

#### Can Modify:
✅ Everything inside **assigned projects:**
  - Schedule/calendar
  - Tasks (create, assign, modify, delete)
  - Change orders (create, submit for approval)
  - Materials (request, allocate)
  - Photos (upload, organize, approve for client)
  - Progress updates
  - Client communication
  - Create invoices
  - Update budgets (within project scope)

❌ **Cannot Modify:**
- Global finances
- Other PM projects
- System settings
- User roles
- Company-wide policies

#### Special Privileges:
- Send external emails (clients, vendors)
- Create and approve change orders
- Generate invoices
- Approve employee timesheets for their projects
- Assign tasks to employees
- Upload client-facing photos

---

### 3. PM TRAINEE

**Role Code:** `pm_trainee`  
**Permission Count:** 33 permissions  
**Custom Permissions:** ❌ NO `can_send_external_emails`

#### Can See:
Same as PM Full for assigned projects

#### Can Modify:
✅ Same as PM Full EXCEPT:
- **Cannot send external emails**
- Invoices auto-marked as `is_draft_for_review=True`
- Change orders require senior PM approval

❌ **Cannot:**
- Send emails to clients
- Send emails to vendors
- Finalize invoices (require admin review)
- Make financial commitments

#### Special Restrictions:
- All external communication must go through Admin or PM Full
- Invoices created are automatically flagged for review
- Cannot approve change orders above certain threshold
- Training mode: actions logged with extra detail

---

### 4. DESIGNER

**Role Code:** `designer`  
**Permission Count:** 14 permissions  
**Custom Permissions:** None

#### Can See:
✅ Projects assigned to them  
✅ Color samples  
✅ Design-related tasks  
✅ Floor plans  
✅ Material specifications  
✅ Design-related photos

❌ **Cannot See:**
- Financial data
- Employee data
- Full project calendar
- Internal PM notes
- Client private information

#### Can Modify:
✅ Color samples (create, edit, submit for approval)  
✅ Floor plan pins (create design notes)  
✅ Design tasks (update progress)  
✅ Upload design-related photos

❌ **Cannot Modify:**
- Project schedule
- Financial data
- Task assignments
- Client communication

#### Special Privileges:
- Access to design tools
- Color sample workflow
- Material specification
- Can create visual pins on floor plans

---

### 5. SUPERINTENDENT

**Role Code:** `superintendent`  
**Permission Count:** 11 permissions  
**Custom Permissions:** None

#### Can See:
✅ Field operations for assigned projects  
✅ Daily schedules  
✅ Employee assignments  
✅ Material inventory on-site  
✅ Safety documentation  
✅ Task progress

❌ **Cannot See:**
- Financial data (except material needs)
- Client private information
- Other project details
- Payroll

#### Can Modify:
✅ Daily task assignments  
✅ Employee check-in/check-out  
✅ Safety reports  
✅ Material requests  
✅ Progress photos  
✅ Field notes

❌ **Cannot Modify:**
- Master schedule
- Budgets
- Client communication
- Financial transactions

#### Special Privileges:
- Field-level oversight
- Employee coordination
- Safety enforcement
- Quality control checks

---

### 6. EMPLOYEE

**Role Code:** `employee`  
**Permission Count:** 3 permissions  
**Custom Permissions:** None

#### Can See:
✅ **Only their assigned tasks**  
✅ Instructions for their tasks  
✅ SOPs related to their work  
✅ Their schedule  
✅ Their timesheet  
✅ Materials needed for their tasks

❌ **Cannot See:**
- Other employees' tasks
- Financial data
- Project budgets
- Client information
- Full project calendar
- Other projects
- Company-wide data

#### Can Modify:
✅ **Only their own progress:**
  - Mark tasks as done
  - Upload photos for their tasks
  - Log notes on their work
  - Report issues/blockers
  - Clock in/out
  - Request materials
  - Request reimbursements

❌ **Cannot Modify:**
- Schedules
- Task assignments
- Other employees' data
- Projects
- Clients
- Financials

#### Special Restrictions:
- Mobile-first experience
- Simplified interface
- Task-focused view only
- Cannot see bigger picture
- Limited to "need-to-know" only

---

### 7. CLIENT

**Role Code:** `client`  
**Permission Count:** 9 permissions  
**Custom Permissions:** None

#### Can See:
✅ **Full project timeline** (except internal notes)  
✅ Estimates for their projects  
✅ Change orders  
✅ Invoices  
✅ Progress photos and notes (admin-approved only)  
✅ All events relevant to their project  
✅ Project calendar (no internal team data)  
✅ Milestones and deadlines  
✅ Payment history

❌ **Cannot See:**
- Internal finances (costs, margins, profit)
- Payroll data
- Internal materials costs
- PM notes (internal)
- Employee tasks (internal assignments)
- Other projects
- Employee personal data
- Vendor communications

#### Can Modify:
✅ Approve/reject change orders  
✅ Add comments, files, photos  
✅ Comment on calendar events  
✅ Request updates  
✅ Update their contact information

❌ **Cannot:**
- Delete items (admin approval required)
- Modify schedules
- Modify budgets
- Assign tasks
- Access internal operations
- See other clients' data

#### Special Privileges:
- Client portal access
- Change order approval
- Invoice review
- Progress visibility
- Document sharing

---

## PERMISSION MATRIX

### Module: Projects

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View All Projects** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Assigned Projects** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Create Project** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Edit Project** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Delete Project** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Close Project** | ✅ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Project Financials** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ⚠️² |

¹ Only for assigned projects  
² Only invoices and change orders, no internal costs

---

### Module: Calendar / Schedule

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View All Calendars** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Assigned Calendar** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅³ | ✅⁴ |
| **Create Events** | ✅ | ✅¹ | ✅¹ | ❌ | ✅¹ | ❌ | ❌ |
| **Modify Events (Drag/Drop)** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Delete Events** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Comment on Events** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Sync External Calendar** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

³ Only their own tasks  
⁴ Only project milestones, no internal tasks

---

### Module: Tasks / Assignments

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View All Tasks** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Assigned Tasks** | ✅ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅⁵ | ❌ |
| **Create Tasks** | ✅ | ✅¹ | ✅¹ | ❌ | ✅¹ | ❌ | ❌ |
| **Assign Tasks** | ✅ | ✅¹ | ✅¹ | ❌ | ✅¹ | ❌ | ❌ |
| **Modify Tasks** | ✅ | ✅¹ | ✅¹ | ✅⁶ | ✅¹ | ✅⁷ | ❌ |
| **Delete Tasks** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Mark Complete** | ✅ | ✅ | ✅ | ✅⁶ | ✅ | ✅⁵ | ❌ |
| **Upload Photos** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅⁵ | ✅⁸ |

⁵ Only their assigned tasks  
⁶ Only design-related tasks  
⁷ Can only update progress, not reassign  
⁸ Can upload photos to their project

---

### Module: Financials

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View All Financials** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Project Financials** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ⚠️² |
| **Create Invoice** | ✅ | ✅¹ | ⚠️⁹ | ❌ | ❌ | ❌ | ❌ |
| **Edit Invoice** | ✅ | ✅¹ | ⚠️⁹ | ❌ | ❌ | ❌ | ❌ |
| **Delete Invoice** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Send Invoice** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Mark Invoice Paid** | ✅ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Internal Costs** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Modify Budgets** | ✅ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Reports** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |

⁹ Auto-marked as draft, requires admin approval

---

### Module: Change Orders

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View Change Orders** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ✅¹ |
| **Create Change Order** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Edit Change Order** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Delete Change Order** | ✅ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Submit for Approval** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Approve Change Order** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅¹⁰ |
| **Reject Change Order** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅¹⁰ |

¹⁰ Client approves/rejects their own project's COs

---

### Module: Inventory / Materials

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View All Inventory** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Project Inventory** | ✅ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ⚠️¹¹ | ❌ |
| **Add Inventory** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |
| **Transfer Inventory** | ✅ | ✅¹ | ✅¹ | ❌ | ✅¹ | ❌ | ❌ |
| **Bulk Transfer** | ✅ | ✅¹ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Request Materials** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **View Material Costs** | ✅ | ✅¹ | ✅¹ | ❌ | ❌ | ❌ | ❌ |

¹¹ Only materials needed for their tasks

---

### Module: Notifications

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **Receive Notifications** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Configure Preferences** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Send System Notifications** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Send Project Notifications** | ✅ | ✅¹ | ⚠️¹² | ❌ | ❌ | ❌ | ❌ |

¹² Internal only, no external emails

---

### Module: AI Assistant

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **Use AI Quick Mode** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **AI Task Generation** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **AI Risk Alerts** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **AI Recommendations** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Approve AI Actions** | ✅ | ✅ | ⚠️¹³ | ❌ | ❌ | ❌ | ❌ |

¹³ Limited approval authority

---

### Module: Users & System

| Action | Admin | PM Full | PM Trainee | Designer | Super | Employee | Client |
|--------|-------|---------|------------|----------|-------|----------|--------|
| **View All Users** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Team Members** | ✅ | ✅¹⁴ | ✅¹⁴ | ❌ | ✅¹⁴ | ❌ | ❌ |
| **Create Users** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Edit User Roles** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Delete Users** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View System Settings** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Modify System Settings** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Audit Logs** | ✅ | ⚠️¹⁵ | ❌ | ❌ | ❌ | ❌ | ❌ |

¹⁴ Only team members on their projects  
¹⁵ Only for their own projects

---

## IMPLEMENTATION NOTES

### API Enforcement
```python
from core.permissions import require_role, require_permission

@require_role(['admin', 'project_manager_full'])
def create_project(request):
    # Only Admin and PM Full can create projects
    pass

@require_permission('core.can_send_external_emails')
def send_client_email(request):
    # Only users with email permission
    pass
```

### Frontend Enforcement
```javascript
// Vue.js example
<template>
  <button v-if="canSendEmails">Send Email</button>
</template>

<script>
computed: {
  canSendEmails() {
    return this.$store.getters.hasPermission('can_send_external_emails')
  }
}
</script>
```

### Database Query Filtering
```python
# Auto-filter based on role
if user.role == 'project_manager_full':
    projects = Project.objects.filter(assigned_pms=user)
elif user.role == 'employee':
    tasks = Task.objects.filter(assigned_to=user)
elif user.role == 'client':
    projects = Project.objects.filter(client=user.client_profile)
```

---

## AUDIT & COMPLIANCE

### All Actions Logged
Every permission-gated action is logged:
- User ID and role
- Action performed
- Resource affected
- Timestamp
- IP address
- Result (success/failure)

### Permission Changes
- Role changes require Admin approval
- All role changes logged
- Email notification on role change
- Permission grants expire (optional)

---

## TESTING PERMISSIONS

### Permission Test Suite
All roles must pass permission tests:
- Can access allowed endpoints
- Cannot access forbidden endpoints
- UI elements hidden appropriately
- Database queries filtered correctly

### Test Command
```bash
python manage.py test core.tests.test_permissions --verbosity=2
```

---

## CROSS-REFERENCES

- See **REQUIREMENTS_OVERVIEW.md** for functional requirements
- See **ARCHITECTURE_UNIFIED.md** for system architecture
- See **API_ENDPOINTS_REFERENCE.md** for API-level permissions
- See **SECURITY_COMPREHENSIVE.md** for security implementation

---

**Document Control:**
- Version: 1.0
- Status: Official Master Document #4 of 9
- Owner Approved: December 8, 2025
- Last Audit: December 8, 2025

