# API ENDPOINTS REFERENCE
**System:** Kibray ERP  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## TABLE OF CONTENTS

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Projects API](#projects-api)
5. [Calendar API](#calendar-api)
6. [Tasks API](#tasks-api)
7. [Financial API](#financial-api)
8. [Change Orders API](#change-orders-api)
9. [Inventory API](#inventory-api)
10. [Notifications API](#notifications-api)
11. [AI API](#ai-api)
12. [Users & Auth API](#users--auth-api)
13. [Error Handling](#error-handling)
14. [Rate Limiting](#rate-limiting)

---

## API OVERVIEW

### Base URL
```
Production: https://kibray.up.railway.app/api/
Development: http://localhost:8000/api/
```

### API Version
Current Version: `v1`

All endpoints are prefixed with `/api/v1/`

### Response Format
All responses are JSON with consistent structure:

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2025-12-08T10:30:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2025-12-08T10:30:00Z"
}
```

---

## AUTHENTICATION

### Method
JWT (JSON Web Token) authentication

### Obtaining Token
**POST /api/auth/login/**

**Request:**
```json
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "username": "user@example.com",
      "role": "project_manager_full"
    }
  }
}
```

### Using Token
Include in Authorization header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Refreshing Token
**POST /api/auth/refresh/**

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 3600
}
```

---

## COMMON PATTERNS

### Pagination
All list endpoints support pagination:

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

**Response Structure:**
```json
{
  "success": true,
  "data": {
    "results": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_pages": 5,
      "total_count": 97,
      "next": "/api/projects/?page=2",
      "previous": null
    }
  }
}
```

### Filtering
Use query parameters for filtering:
```
GET /api/projects/?status=active&assigned_pm=user_id
```

### Sorting
Use `ordering` parameter:
```
GET /api/tasks/?ordering=-created_at
GET /api/tasks/?ordering=due_date,-priority
```

Prefix with `-` for descending order.

### Field Selection
Use `fields` parameter to request specific fields:
```
GET /api/projects/?fields=id,name,status
```

---

## PROJECTS API

### List Projects
**GET /api/projects/**

**Permissions:** 
- Admin: All projects
- PM: Assigned projects only
- Client: Their projects only

**Query Parameters:**
- `status` - Filter by status (created, active, closed)
- `assigned_pm` - Filter by PM ID
- `client` - Filter by client ID
- `search` - Search by name or description

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "name": "Kitchen Renovation",
        "client": {
          "id": "uuid",
          "name": "John Doe"
        },
        "status": "active",
        "assigned_pms": [
          {
            "id": "uuid",
            "name": "Jane Smith"
          }
        ],
        "budget": "50000.00",
        "start_date": "2025-01-15",
        "end_date": "2025-03-15",
        "progress_percent": 45
      }
    ],
    "pagination": { ... }
  }
}
```

### Get Project Detail
**GET /api/projects/{id}/**

**Permissions:** Admin, Assigned PM, Client (own project)

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Kitchen Renovation",
    "description": "Complete kitchen remodel",
    "client": { ... },
    "status": "active",
    "assigned_pms": [ ... ],
    "budget": "50000.00",
    "start_date": "2025-01-15",
    "end_date": "2025-03-15",
    "location": {
      "address": "123 Main St",
      "city": "Austin",
      "state": "TX",
      "zip": "78701"
    },
    "profitability": {
      "total_invoiced": "45000.00",
      "total_paid": "40000.00",
      "total_expenses": "32000.00",
      "profit": "8000.00",
      "roi": 25.0
    },
    "created_at": "2025-01-10T10:00:00Z",
    "updated_at": "2025-12-08T10:00:00Z"
  }
}
```

### Create Project
**POST /api/projects/**

**Permissions:** Admin, PM Full, PM Trainee

**Request:**
```json
{
  "name": "New Project",
  "client_id": "uuid",
  "description": "Project description",
  "budget": "75000.00",
  "start_date": "2025-02-01",
  "end_date": "2025-05-01",
  "location": {
    "address": "456 Oak Ave",
    "city": "Austin",
    "state": "TX",
    "zip": "78702"
  },
  "assigned_pm_ids": ["uuid1", "uuid2"]
}
```

**Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Project created successfully"
}
```

### Update Project
**PUT /api/projects/{id}/**
**PATCH /api/projects/{id}/** (partial update)

**Permissions:** Admin, Assigned PM

**Request (PATCH example):**
```json
{
  "status": "active",
  "end_date": "2025-05-15"
}
```

### Delete Project
**DELETE /api/projects/{id}/**

**Permissions:** Admin only

---

## CALENDAR API

### List Events
**GET /api/calendar/events/**

**Permissions:** Role-filtered visibility

**Query Parameters:**
- `project_id` - Filter by project
- `start_date` - Events starting after date
- `end_date` - Events ending before date
- `event_type` - Filter by type
- `assigned_to` - Filter by assigned user

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "title": "Foundation Pour",
        "description": "Pour concrete foundation",
        "start_datetime": "2025-01-20T08:00:00Z",
        "end_datetime": "2025-01-20T16:00:00Z",
        "all_day": false,
        "event_type": "task",
        "status": "scheduled",
        "project": {
          "id": "uuid",
          "name": "Kitchen Renovation"
        },
        "assigned_to": [
          {
            "id": "uuid",
            "name": "John Worker"
          }
        ],
        "is_visible_to_client": true,
        "ai_risk_level": "none",
        "ai_conflicts": []
      }
    ]
  }
}
```

### Create Event
**POST /api/calendar/events/**

**Permissions:** Admin, PM Full, PM Trainee

**Request:**
```json
{
  "title": "Site Inspection",
  "description": "Final walkthrough with client",
  "start_datetime": "2025-01-25T10:00:00Z",
  "end_datetime": "2025-01-25T12:00:00Z",
  "all_day": false,
  "event_type": "inspection",
  "project_id": "uuid",
  "assigned_to_ids": ["uuid1", "uuid2"],
  "is_visible_to_client": true
}
```

### Update Event (Drag & Drop)
**PATCH /api/calendar/events/{id}/move/**

**Permissions:** Admin, Assigned PM

**Request:**
```json
{
  "start_datetime": "2025-01-26T10:00:00Z",
  "end_datetime": "2025-01-26T12:00:00Z"
}
```

### Sync External Calendar
**POST /api/calendar/events/{id}/sync/**

**Permissions:** Admin, PM Full, PM Trainee

**Request:**
```json
{
  "sync_to": ["google", "apple"]
}
```

### Get Conflicts
**GET /api/calendar/conflicts/**

**Permissions:** Admin, PM

**Query Parameters:**
- `project_id` - Project to analyze
- `start_date` - Analysis start date
- `end_date` - Analysis end date

**Response:**
```json
{
  "success": true,
  "data": {
    "conflicts": [
      {
        "type": "resource_conflict",
        "severity": "high",
        "events": [
          {
            "id": "uuid1",
            "title": "Event 1"
          },
          {
            "id": "uuid2",
            "title": "Event 2"
          }
        ],
        "message": "2 events overlap for same resource",
        "recommendation": "Reassign one event to different team member"
      }
    ]
  }
}
```

---

## TASKS API

### List Tasks
**GET /api/tasks/**

**Permissions:** Role-filtered

**Query Parameters:**
- `project_id` - Filter by project
- `assigned_to` - Filter by assigned user
- `status` - Filter by status
- `due_date_from` - Tasks due after date
- `due_date_to` - Tasks due before date
- `is_overdue` - Boolean filter

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "title": "Install cabinets",
        "description": "Install kitchen cabinets",
        "project": { ... },
        "assigned_to": [ ... ],
        "status": "in_progress",
        "priority": "high",
        "schedule_weight": 80,
        "progress_percent": 50,
        "estimated_hours": 8,
        "actual_hours": 4.5,
        "due_date": "2025-01-22",
        "is_overdue": false,
        "checklist": [
          {"item": "Measure wall", "checked": true},
          {"item": "Mount upper cabinets", "checked": false}
        ]
      }
    ]
  }
}
```

### Create Task
**POST /api/tasks/**

**Permissions:** Admin, PM

**Request:**
```json
{
  "title": "Paint walls",
  "description": "Paint all walls white",
  "project_id": "uuid",
  "assigned_to_ids": ["uuid"],
  "status": "pending",
  "priority": "medium",
  "schedule_weight": 60,
  "estimated_hours": 6,
  "due_date": "2025-01-25",
  "checklist": [
    {"item": "Apply primer", "checked": false},
    {"item": "First coat", "checked": false},
    {"item": "Second coat", "checked": false}
  ]
}
```

### Update Task Progress
**PATCH /api/tasks/{id}/progress/**

**Permissions:** Admin, PM, Assigned Employee

**Request:**
```json
{
  "progress_percent": 75,
  "actual_hours": 5.5,
  "notes": "Progress update"
}
```

### Mark Task Complete
**POST /api/tasks/{id}/complete/**

**Permissions:** Admin, PM, Assigned Employee

**Request:**
```json
{
  "completion_notes": "Task completed successfully",
  "completion_photo": "base64_image_data"
}
```

**Response:**
Automatically hides associated pins if task reaches 100%.

---

## FINANCIAL API

### List Invoices
**GET /api/financials/invoices/**

**Permissions:** Role-filtered (Admin: all, PM: assigned projects, Client: their project)

**Query Parameters:**
- `project_id` - Filter by project
- `status` - Filter by status
- `invoice_type` - Filter by type
- `is_overdue` - Boolean filter

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "invoice_number": "INV-2025-001",
        "invoice_type": "standard",
        "status": "SENT",
        "project": { ... },
        "client": { ... },
        "subtotal": "10000.00",
        "tax_rate": "8.25",
        "tax_amount": "825.00",
        "total_amount": "10825.00",
        "retention_amount": "541.25",
        "amount_paid": "0.00",
        "net_payable": "10283.75",
        "issue_date": "2025-01-15",
        "due_date": "2025-02-15",
        "is_draft_for_review": false
      }
    ]
  }
}
```

### Create Invoice
**POST /api/financials/invoices/**

**Permissions:** Admin, PM Full, PM Trainee (auto-draft)

**Request:**
```json
{
  "project_id": "uuid",
  "invoice_type": "standard",
  "issue_date": "2025-01-15",
  "due_date": "2025-02-15",
  "retention_amount": "500.00",
  "line_items": [
    {
      "description": "Labor - Week 1",
      "quantity": 40,
      "unit_price": "50.00",
      "tax_rate": "8.25"
    },
    {
      "description": "Materials",
      "quantity": 1,
      "unit_price": "5000.00",
      "tax_rate": "8.25"
    }
  ]
}
```

**Note:** PM Trainee invoices automatically marked `is_draft_for_review=true`

### Mark Invoice Paid
**POST /api/financials/invoices/{id}/mark-paid/**

**Permissions:** Admin, PM Full

**Request:**
```json
{
  "amount_paid": "10825.00",
  "payment_date": "2025-02-10",
  "payment_method": "check",
  "payment_reference": "CHK-5678"
}
```

### Get Profitability Report
**GET /api/financials/profitability/{project_id}/**

**Permissions:** Admin, Assigned PM

**Response:**
```json
{
  "success": true,
  "data": {
    "project": { ... },
    "total_invoiced": "45000.00",
    "total_paid": "40000.00",
    "total_expenses": "32000.00",
    "profit": "8000.00",
    "roi": 25.0,
    "budget": "50000.00",
    "budget_variance": "18000.00",
    "budget_variance_pct": 36.0,
    "expense_breakdown": {
      "MATERIALS": "20000.00",
      "LABOR": "10000.00",
      "EQUIPMENT": "2000.00"
    }
  }
}
```

### List Expenses
**GET /api/financials/expenses/**

**Query Parameters:**
- `project_id` - Filter by project
- `category` - Filter by category
- `reimbursement_status` - Filter by status

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "project": { ... },
        "category": "TOOLS",
        "amount": "150.00",
        "paid_by_company": false,
        "paid_by_employee": {
          "id": "uuid",
          "name": "John Worker"
        },
        "reimbursement_status": "pending",
        "expense_date": "2025-01-18",
        "receipt_url": "https://..."
      }
    ]
  }
}
```

### Reimburse Expense
**POST /api/financials/expenses/{id}/reimburse/**

**Permissions:** Admin only

**Request:**
```json
{
  "method": "paid_direct",
  "reference": "CHK-1234",
  "reimbursement_date": "2025-01-20"
}
```

---

## CHANGE ORDERS API

### List Change Orders
**GET /api/change-orders/**

**Permissions:** Role-filtered

**Query Parameters:**
- `project_id` - Filter by project
- `status` - Filter by status

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "co_number": "CO-2025-001",
        "project": { ... },
        "title": "Add skylight",
        "description": "Client requested skylight in kitchen",
        "status": "pending_approval",
        "cost_impact": "2500.00",
        "timeline_impact_days": 3,
        "created_by": { ... },
        "created_at": "2025-01-16T10:00:00Z"
      }
    ]
  }
}
```

### Create Change Order
**POST /api/change-orders/**

**Permissions:** Admin, PM

**Request:**
```json
{
  "project_id": "uuid",
  "title": "Add skylight",
  "description": "Client requested skylight installation",
  "cost_impact": "2500.00",
  "timeline_impact_days": 3,
  "justification": "Client upgrade request",
  "photos": ["base64_image_1", "base64_image_2"]
}
```

### Client Approve/Reject
**POST /api/change-orders/{id}/approve/**
**POST /api/change-orders/{id}/reject/**

**Permissions:** Admin, Client (own project)

**Request (approve):**
```json
{
  "signature": "base64_signature_image",
  "notes": "Approved"
}
```

**Request (reject):**
```json
{
  "reason": "Cost too high"
}
```

---

## INVENTORY API

### List Inventory
**GET /api/inventory/**

**Permissions:** Role-filtered

**Query Parameters:**
- `project_id` - Filter by project
- `category` - Filter by category
- `low_stock` - Boolean (quantity < reorder_point)

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "project": { ... },
        "item_name": "Interior Paint - White",
        "category": "PAINT",
        "quantity": 15.5,
        "unit": "gallons",
        "reserved_quantity": 5.0,
        "available_quantity": 10.5,
        "unit_cost": "35.00",
        "total_value": "542.50"
      }
    ]
  }
}
```

### Transfer Inventory
**POST /api/inventory/transfer/**

**Permissions:** Admin, PM

**Request:**
```json
{
  "from_project_id": "uuid",
  "to_project_id": "uuid",
  "items": [
    {
      "inventory_id": "uuid",
      "quantity": 5.0
    }
  ]
}
```

### Bulk Transfer on Project Close
**POST /api/inventory/bulk-transfer/**

**Permissions:** Admin, PM Full

**Request:**
```json
{
  "project_id": "uuid",
  "categories": ["PAINT", "TOOLS"],
  "exclude_leftover": true,
  "destination": "central_warehouse"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_transferred": "2450.00",
    "items_transferred": 15,
    "excluded_items": 3,
    "movements": [ ... ]
  }
}
```

---

## NOTIFICATIONS API

### List Notifications
**GET /api/notifications/**

**Permissions:** Own notifications only

**Query Parameters:**
- `is_read` - Boolean filter
- `type` - Filter by notification type
- `priority` - Filter by priority

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "type": "task_assigned",
        "title": "New Task Assigned",
        "message": "You have been assigned to 'Install cabinets'",
        "priority": "normal",
        "is_read": false,
        "action_url": "/tasks/uuid",
        "action_text": "View Task",
        "created_at": "2025-01-18T14:30:00Z"
      }
    ],
    "unread_count": 5
  }
}
```

### Mark as Read
**POST /api/notifications/{id}/mark-read/**

**Response:**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

### Mark All as Read
**POST /api/notifications/mark-all-read/**

**Response:**
```json
{
  "success": true,
  "message": "All notifications marked as read",
  "count": 12
}
```

### Update Preferences
**PUT /api/notifications/preferences/**

**Request:**
```json
{
  "task_assigned": {
    "channels": ["in_app", "email"],
    "enabled": true
  },
  "task_due_soon": {
    "channels": ["in_app", "sms"],
    "enabled": true
  },
  "invoice_sent": {
    "channels": ["email"],
    "enabled": false
  }
}
```

---

## AI API

### Get Risk Analysis
**GET /api/ai/risks/{project_id}/**

**Permissions:** Admin, PM

**Response:**
```json
{
  "success": true,
  "data": {
    "project": { ... },
    "risk_summary": {
      "total_risks": 3,
      "critical": 0,
      "high": 1,
      "medium": 2,
      "low": 0
    },
    "risks": [
      {
        "type": "budget_overrun",
        "severity": "high",
        "message": "Budget overrun: -12.5%",
        "recommendation": "Review expenses and consider change order",
        "detected_at": "2025-01-18T10:00:00Z"
      }
    ]
  }
}
```

### Generate Task Suggestions
**POST /api/ai/generate-tasks/**

**Permissions:** Admin, PM

**Request:**
```json
{
  "project_id": "uuid",
  "context": "completed_task",
  "context_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "title": "Apply primer coat",
        "description": "Follow-up to painting prep",
        "estimated_hours": 4,
        "priority": "high",
        "confidence": 0.85
      }
    ]
  }
}
```

### Dashboard Insights
**GET /api/ai/insights/dashboard/**

**Permissions:** Admin, PM

**Response:**
```json
{
  "success": true,
  "data": {
    "active_risks": 8,
    "overdue_tasks": 3,
    "budget_alerts": 2,
    "recommended_actions": [
      {
        "action": "reassign_task",
        "task_id": "uuid",
        "reason": "Resource over-allocated",
        "priority": "high"
      }
    ]
  }
}
```

---

## USERS & AUTH API

### Login
**POST /api/auth/login/**
(See Authentication section)

### Logout
**POST /api/auth/logout/**

**Request:**
```json
{
  "refresh_token": "..."
}
```

### Get Current User
**GET /api/auth/me/**

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "project_manager_full",
    "permissions": [
      "can_send_external_emails",
      "view_project",
      "edit_project"
    ]
  }
}
```

### List Users
**GET /api/users/**

**Permissions:** Admin only

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "username": "jdoe",
        "email": "jdoe@example.com",
        "role": "project_manager_full",
        "is_active": true
      }
    ]
  }
}
```

---

## ERROR HANDLING

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_REQUIRED` | 401 | No valid token provided |
| `PERMISSION_DENIED` | 403 | User lacks required permission |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `SERVER_ERROR` | 500 | Internal server error |

### Error Response Example
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "email": ["This field is required"],
      "budget": ["Must be a positive number"]
    }
  },
  "timestamp": "2025-12-08T10:30:00Z"
}
```

---

## RATE LIMITING

### Limits
- **Authenticated users:** 1000 requests/hour
- **Unauthenticated:** 100 requests/hour
- **Expensive operations:** 10 requests/minute (e.g., reports, AI analysis)

### Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1641650400
```

### Exceeded Response
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 3600
  }
}
```

---

## WEBHOOKS (Future)

Webhook support planned for:
- Task completion
- Invoice payment
- Change order approval
- Project status change

---

## CROSS-REFERENCES

- See **MODULES_SPECIFICATIONS.md** for detailed module specs
- See **ROLE_PERMISSIONS_REFERENCE.md** for permission details
- See **SECURITY_COMPREHENSIVE.md** for security implementation

---

**Document Control:**
- Version: 1.0
- Status: Official Master Document #5 of 9
- Owner Approved: December 8, 2025
- Last Updated: December 8, 2025
