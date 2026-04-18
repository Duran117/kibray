# MODULES SPECIFICATIONS
**System:** Kibray ERP  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## TABLE OF CONTENTS

1. [Module Overview](#module-overview)
2. [Calendar & Schedule System](#calendar--schedule-system)
3. [Financial Module](#financial-module)
4. [AI Quick Mode](#ai-quick-mode)
5. [Notifications System](#notifications-system)
6. [Strategic Planner](#strategic-planner)
7. [WebSocket & Real-Time](#websocket--real-time)
8. [Wizards System](#wizards-system)
9. [Project Management](#project-management)
10. [Task & Assignment System](#task--assignment-system)
11. [Change Orders](#change-orders)
12. [Estimates & Proposals](#estimates--proposals)
13. [Inventory Management](#inventory-management)
14. [Visual Collaboration](#visual-collaboration)
15. [SOP System](#sop-system)
16. [Client Portal](#client-portal)

---

## MODULE OVERVIEW

This document provides detailed technical specifications for all system modules, including database schemas, business logic, API contracts, and integration points.

### Module Priority Levels

**HIGH PRIORITY:**
- Calendar/Schedule System
- Financial Module
- AI Quick Mode
- Notifications System
- Strategic Planner
- Wizards
- WebSocket/Real-Time

**MEDIUM PRIORITY:**
- SOP System

**CORE MODULES (Must Preserve):**
- Project Management
- Task & Assignment System
- Change Orders
- Estimates & Proposals
- Inventory Management

---

## CALENDAR & SCHEDULE SYSTEM

### Overview
Modular calendar system with layered role-based visibility, AI-powered insights, and external calendar integration.

### Database Schema

#### CalendarEvent Model
```python
class CalendarEvent(models.Model):
    # Core Fields
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    title = CharField(max_length=255)
    description = TextField(blank=True)
    
    # Timing
    start_datetime = DateTimeField()
    end_datetime = DateTimeField()
    all_day = BooleanField(default=False)
    
    # Relations
    project = ForeignKey('Project', on_delete=CASCADE, related_name='events')
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    assigned_to = ManyToManyField(User, related_name='assigned_events', blank=True)
    
    # Type & Status
    event_type = CharField(max_length=50, choices=EVENT_TYPES)
    status = CharField(max_length=50, choices=EVENT_STATUS)
    
    # Visibility
    is_visible_to_client = BooleanField(default=False)
    visibility_level = CharField(max_length=50, choices=VISIBILITY_LEVELS)
    
    # External Sync
    google_event_id = CharField(max_length=255, blank=True, null=True)
    apple_event_id = CharField(max_length=255, blank=True, null=True)
    sync_status = CharField(max_length=50, default='not_synced')
    last_synced = DateTimeField(null=True, blank=True)
    
    # AI Insights
    ai_risk_level = CharField(max_length=50, choices=RISK_LEVELS, default='none')
    ai_conflicts = JSONField(default=list, blank=True)
    ai_recommendations = JSONField(default=list, blank=True)
    
    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**EVENT_TYPES:**
- `milestone` - Project milestone
- `task` - Scheduled task
- `meeting` - Team or client meeting
- `deadline` - Hard deadline
- `reminder` - Reminder/notification
- `phase_start` - Phase beginning
- `phase_end` - Phase completion
- `inspection` - Inspection or review
- `delivery` - Material or equipment delivery

**EVENT_STATUS:**
- `scheduled` - Planned event
- `in_progress` - Currently happening
- `completed` - Finished
- `cancelled` - Cancelled
- `rescheduled` - Moved to new time

**VISIBILITY_LEVELS:**
- `admin_only` - Admin only
- `internal` - All internal staff
- `project_team` - Project team members
- `client_visible` - Visible to client

**RISK_LEVELS:**
- `none` - No risk detected
- `low` - Minor concern
- `medium` - Moderate risk
- `high` - Significant risk
- `critical` - Critical issue

### Business Logic

#### Conflict Detection
```python
def detect_conflicts(self):
    """AI-powered conflict detection"""
    conflicts = []
    
    # Resource over-allocation
    overlapping_events = CalendarEvent.objects.filter(
        assigned_to__in=self.assigned_to.all(),
        start_datetime__lt=self.end_datetime,
        end_datetime__gt=self.start_datetime
    ).exclude(id=self.id)
    
    if overlapping_events.exists():
        conflicts.append({
            'type': 'resource_conflict',
            'severity': 'high',
            'message': f'{overlapping_events.count()} overlapping events'
        })
    
    # Weather risk (for outdoor work)
    if self.event_type in ['task', 'phase_start'] and self.project.is_outdoor:
        weather_risk = check_weather_forecast(
            self.project.location, 
            self.start_datetime
        )
        if weather_risk['severity'] > 0.5:
            conflicts.append({
                'type': 'weather_risk',
                'severity': 'medium',
                'message': weather_risk['description']
            })
    
    # Dependency issues
    if self.dependencies.exists():
        incomplete_deps = self.dependencies.filter(status__ne='completed')
        if incomplete_deps.exists():
            conflicts.append({
                'type': 'dependency_not_met',
                'severity': 'critical',
                'message': f'{incomplete_deps.count()} dependencies incomplete'
            })
    
    self.ai_conflicts = conflicts
    self.ai_risk_level = self._calculate_risk_level(conflicts)
    return conflicts

def _calculate_risk_level(self, conflicts):
    """Calculate overall risk from conflicts"""
    if not conflicts:
        return 'none'
    
    severities = [c['severity'] for c in conflicts]
    if 'critical' in severities:
        return 'critical'
    elif 'high' in severities:
        return 'high'
    elif 'medium' in severities:
        return 'medium'
    else:
        return 'low'
```

#### External Calendar Sync
```python
def sync_to_google_calendar(self):
    """Sync event to Google Calendar"""
    from integrations.google_calendar import GoogleCalendarAPI
    
    api = GoogleCalendarAPI(user=self.created_by)
    
    if self.google_event_id:
        # Update existing
        result = api.update_event(self.google_event_id, self._to_google_format())
    else:
        # Create new
        result = api.create_event(self._to_google_format())
        self.google_event_id = result['id']
    
    self.sync_status = 'synced'
    self.last_synced = timezone.now()
    self.save()

def sync_from_google_calendar(self, google_event_data):
    """Import changes from Google Calendar"""
    # Merge logic with conflict resolution
    if self.updated_at > google_event_data['updated']:
        # Local is newer, push to Google
        self.sync_to_google_calendar()
    else:
        # Google is newer, pull from Google
        self.title = google_event_data['summary']
        self.start_datetime = parse_datetime(google_event_data['start'])
        self.end_datetime = parse_datetime(google_event_data['end'])
        self.sync_status = 'synced'
        self.last_synced = timezone.now()
        self.save()
```

### Views & Filters

#### Timeline View (Gantt)
- Projects as rows
- Time as columns
- Drag & drop support (PM/Admin only)
- Dependency lines
- Critical path highlighting
- Milestone markers

#### Daily View
- List of today's events
- Grouped by time
- Employee assignments
- Quick status updates

#### Weekly View
- 7-day overview
- Resource allocation view
- Capacity planning
- Conflict indicators

#### Monthly View
- Calendar grid
- Milestone view
- Capacity heatmap
- Phase boundaries

### API Endpoints

**GET /api/calendar/events/**
- List all events (filtered by role)
- Query params: project_id, start_date, end_date, event_type

**POST /api/calendar/events/**
- Create new event
- Permissions: Admin, PM Full, PM Trainee

**PUT /api/calendar/events/{id}/**
- Update event
- Drag & drop uses this endpoint
- Permissions: Admin, PM (assigned project only)

**DELETE /api/calendar/events/{id}/**
- Delete event
- Permissions: Admin, PM (assigned project only)

**POST /api/calendar/events/{id}/sync/**
- Trigger external calendar sync
- Permissions: Admin, PM Full, PM Trainee

**GET /api/calendar/conflicts/**
- Get all detected conflicts
- AI-powered analysis
- Permissions: Admin, PM

---

## FINANCIAL MODULE

### Overview
Complete financial management system with strict role-based visibility, profitability tracking, and AI-assisted automation.

### Database Schema

#### Invoice Model
```python
class Invoice(models.Model):
    # Core
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    invoice_number = CharField(max_length=50, unique=True)
    
    # Type & Status
    invoice_type = CharField(max_length=50, choices=[
        ('standard', 'Standard Progress Billing'),
        ('deposit', 'Deposit/Advance Payment'),
        ('final', 'Final Invoice with Retention')
    ])
    status = CharField(max_length=50, choices=[
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Client'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ])
    
    # Relations
    project = ForeignKey('Project', on_delete=CASCADE)
    client = ForeignKey('Client', on_delete=CASCADE)
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    
    # Amounts
    subtotal = DecimalField(max_digits=10, decimal_places=2)
    tax_rate = DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = DecimalField(max_digits=10, decimal_places=2)
    total_amount = DecimalField(max_digits=10, decimal_places=2)
    retention_amount = DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Tracking
    amount_paid = DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = DateField(null=True, blank=True)
    
    # PM Trainee Workflow
    is_draft_for_review = BooleanField(default=False)
    reviewed_by = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True, related_name='reviewed_invoices')
    
    # Dates
    issue_date = DateField()
    due_date = DateField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### InvoiceLineItem Model
```python
class InvoiceLineItem(models.Model):
    invoice = ForeignKey(Invoice, on_delete=CASCADE, related_name='line_items')
    description = CharField(max_length=500)
    quantity = DecimalField(max_digits=10, decimal_places=2)
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    line_total = DecimalField(max_digits=10, decimal_places=2)
    tax_rate = DecimalField(max_digits=5, decimal_places=2, default=0)
```

#### Expense Model (with Reimbursements)
```python
class Expense(models.Model):
    # Core
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Relations
    project = ForeignKey('Project', on_delete=CASCADE, related_name='expenses')
    category = CharField(max_length=100, choices=EXPENSE_CATEGORIES)
    
    # Payment Info
    amount = DecimalField(max_digits=10, decimal_places=2)
    paid_by_company = BooleanField(default=True)
    paid_by_employee = ForeignKey('Employee', on_delete=SET_NULL, null=True, blank=True)
    
    # Reimbursement Tracking
    reimbursement_status = CharField(max_length=50, choices=[
        ('not_applicable', 'Not Applicable'),
        ('pending', 'Pending Reimbursement'),
        ('paid_direct', 'Paid Directly'),
        ('next_paycheck', 'Added to Next Paycheck'),
        ('petty_cash', 'Paid via Petty Cash')
    ], default='not_applicable')
    reimbursement_date = DateField(null=True, blank=True)
    reimbursement_reference = CharField(max_length=255, blank=True)
    
    # Documentation
    receipt = FileField(upload_to='receipts/', null=True, blank=True)
    notes = TextField(blank=True)
    
    # Dates
    expense_date = DateField()
    created_at = DateTimeField(auto_now_add=True)
```

**EXPENSE_CATEGORIES:**
- `MATERIALS` - Construction materials
- `LABOR` - Labor costs
- `EQUIPMENT` - Equipment rental
- `TOOLS` - Tool purchases
- `SUBCONTRACTOR` - Subcontractor payments
- `PERMITS` - Permits and fees
- `INSURANCE` - Insurance costs
- `OVERHEAD` - General overhead

### Business Logic

#### Invoice Calculations
```python
def calculate_net_payable(self):
    """Calculate net amount client owes"""
    return self.total_amount - self.retention_amount - self.amount_paid

def mark_for_review(self, user):
    """PM Trainee invoice workflow"""
    if not user.has_perm('core.can_send_external_emails'):
        self.is_draft_for_review = True
        self.status = 'DRAFT'
        
        # Notify admins
        Notification.objects.create(
            type='invoice_review_needed',
            user=admin_user,
            message=f'Invoice {self.invoice_number} needs review'
        )
```

#### Expense Reimbursement
```python
def save(self, *args, **kwargs):
    """Auto-assign reimbursement status"""
    if self.paid_by_employee and self.reimbursement_status == 'not_applicable':
        self.reimbursement_status = 'pending'
    super().save(*args, **kwargs)

def mark_reimbursed(self, method='paid_direct', reference='', user=None):
    """Mark expense as reimbursed"""
    self.reimbursement_status = method
    self.reimbursement_date = timezone.now().date()
    self.reimbursement_reference = reference
    self.save()
    
    # Create audit log
    AuditLog.objects.create(
        action='expense_reimbursed',
        model='Expense',
        object_id=self.id,
        user=user,
        details={'method': method, 'reference': reference}
    )
```

#### Profitability Calculations
```python
class Project:
    def calculate_profitability(self):
        """Calculate project profitability metrics"""
        # Income
        total_invoiced = self.invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_paid = self.invoices.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # Expenses
        total_expenses = self.expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Calculations
        profit = total_paid - total_expenses
        roi = (profit / total_expenses * 100) if total_expenses > 0 else 0
        
        # Budget variance
        budget_variance = self.budget - total_expenses if self.budget else None
        budget_variance_pct = (budget_variance / self.budget * 100) if self.budget else None
        
        return {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_expenses': total_expenses,
            'profit': profit,
            'roi': roi,
            'budget': self.budget,
            'budget_variance': budget_variance,
            'budget_variance_pct': budget_variance_pct
        }
```

### API Endpoints

**GET /api/financials/invoices/**
- List invoices (role-filtered)
- Admin: all, PM: assigned projects, Client: their project

**POST /api/financials/invoices/**
- Create invoice
- Auto-draft for PM Trainee

**GET /api/financials/profitability/{project_id}/**
- Project profitability report
- Admin & PM only

**POST /api/financials/expenses/{id}/reimburse/**
- Mark expense as reimbursed
- Admin only

---

## AI QUICK MODE

### Overview
Intelligent assistant providing proactive monitoring, risk detection, and automated task generation.

### AI Capabilities

#### 1. Risk Detection
```python
class AIRiskDetector:
    def analyze_project(self, project):
        """Comprehensive project risk analysis"""
        risks = []
        
        # Budget risk
        profitability = project.calculate_profitability()
        if profitability['budget_variance_pct'] < -10:
            risks.append({
                'type': 'budget_overrun',
                'severity': 'high',
                'message': f'Budget overrun: {profitability["budget_variance_pct"]:.1f}%',
                'recommendation': 'Review expenses and consider change order'
            })
        
        # Schedule risk
        overdue_tasks = project.tasks.filter(
            due_date__lt=timezone.now(),
            status__ne='completed'
        )
        if overdue_tasks.count() > 3:
            risks.append({
                'type': 'schedule_delay',
                'severity': 'medium',
                'message': f'{overdue_tasks.count()} overdue tasks',
                'recommendation': 'Reassign resources or extend timeline'
            })
        
        # Resource risk
        resource_conflicts = self._detect_resource_conflicts(project)
        if resource_conflicts:
            risks.append({
                'type': 'resource_conflict',
                'severity': 'high',
                'message': 'Resource over-allocation detected',
                'recommendation': 'Rebalance employee assignments'
            })
        
        # Weather risk (for outdoor projects)
        if project.is_outdoor:
            weather_risks = self._check_weather_forecast(project)
            risks.extend(weather_risks)
        
        return risks
```

#### 2. Auto-Generation
```python
class AITaskGenerator:
    def generate_follow_up_tasks(self, completed_task):
        """Generate logical follow-up tasks"""
        suggestions = []
        
        # Example: Task completed = "Painting prep"
        if 'prep' in completed_task.title.lower() and 'paint' in completed_task.title.lower():
            suggestions.append({
                'title': 'Apply primer coat',
                'description': f'Follow-up to: {completed_task.title}',
                'assigned_to': completed_task.assigned_to,
                'estimated_hours': 4,
                'priority': 'high'
            })
        
        return suggestions
    
    def generate_reminders(self, project):
        """Generate intelligent reminders"""
        reminders = []
        
        # Invoice reminder
        unpaid_invoices = project.invoices.filter(
            status='SENT',
            due_date__lt=timezone.now() + timedelta(days=3)
        )
        for invoice in unpaid_invoices:
            reminders.append({
                'type': 'invoice_due_soon',
                'message': f'Invoice {invoice.invoice_number} due in {(invoice.due_date - timezone.now().date()).days} days'
            })
        
        return reminders
```

#### 3. AI Tone & Behavior
- Professional
- Concise
- Clear
- Proactive (intervenes when issues detected)
- Non-emotional

### API Endpoints

**GET /api/ai/risks/{project_id}/**
- Get AI-detected risks for project
- Returns list of risks with severity and recommendations

**POST /api/ai/generate-tasks/**
- AI-generated task suggestions
- Requires approval before creation

**GET /api/ai/insights/dashboard/**
- Dashboard-level AI insights
- System-wide risk overview

---

## NOTIFICATIONS SYSTEM

### Overview
Multi-channel notification delivery with user preferences and intelligent routing.

### Database Schema

```python
class Notification(models.Model):
    # Core
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKey(User, on_delete=CASCADE, related_name='notifications')
    
    # Content
    type = CharField(max_length=100, choices=NOTIFICATION_TYPES)
    title = CharField(max_length=255)
    message = TextField()
    
    # Delivery
    channels = JSONField(default=list)  # ['in_app', 'email', 'sms']
    priority = CharField(max_length=50, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    
    # Status
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)
    
    # Linked Objects
    content_type = ForeignKey(ContentType, on_delete=CASCADE, null=True)
    object_id = PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action
    action_url = CharField(max_length=500, blank=True)
    action_text = CharField(max_length=100, blank=True)
    
    # Timing
    created_at = DateTimeField(auto_now_add=True)
    sent_at = DateTimeField(null=True, blank=True)
```

**NOTIFICATION_TYPES:**
- `task_assigned` - Task assigned to user
- `task_due_soon` - Task due within 24 hours
- `task_overdue` - Task past due date
- `change_order_approval` - CO needs approval
- `invoice_sent` - Invoice sent to client
- `invoice_due` - Invoice due soon
- `budget_alert` - Budget threshold reached
- `schedule_change` - Calendar event modified
- `risk_alert` - AI-detected risk
- `comment_mention` - User mentioned in comment

### Business Logic

```python
class NotificationService:
    def send_notification(self, user, notification_type, data):
        """Send notification via appropriate channels"""
        # Get user preferences
        prefs = user.notification_preferences.get(notification_type, {})
        channels = prefs.get('channels', ['in_app'])
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=self._generate_title(notification_type, data),
            message=self._generate_message(notification_type, data),
            channels=channels,
            priority=self._determine_priority(notification_type)
        )
        
        # Send via each channel
        for channel in channels:
            if channel == 'in_app':
                self._send_in_app(notification)
            elif channel == 'email':
                self._send_email(notification)
            elif channel == 'sms':
                self._send_sms(notification)
            elif channel == 'push':
                self._send_push(notification)
        
        notification.sent_at = timezone.now()
        notification.save()
        
        return notification
```

### WebSocket Real-Time Delivery
```python
# Send via WebSocket for instant delivery
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

async_to_sync(channel_layer.group_send)(
    f'user_{user.id}',
    {
        'type': 'notification',
        'notification': NotificationSerializer(notification).data
    }
)
```

---

## WEBSOCKET & REAL-TIME

### Overview
Django Channels-based WebSocket system for real-time data synchronization.

### Architecture

**Technology Stack:**
- Django Channels 4+
- Redis channel layer
- WebSocket protocol
- Connection pooling

### Consumer Implementation

```python
class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.project_group_name = f'project_{self.project_id}'
        
        # Verify permissions
        user = self.scope['user']
        if not await self.has_project_access(user, self.project_id):
            await self.close()
            return
        
        # Join project group
        await self.channel_layer.group_add(
            self.project_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.project_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'task_update':
            await self.handle_task_update(data)
        elif message_type == 'calendar_update':
            await self.handle_calendar_update(data)
    
    async def task_update(self, event):
        """Send task update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'task': event['task']
        }))
    
    async def calendar_update(self, event):
        """Send calendar update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'calendar_update',
            'event': event['event']
        }))
```

### Broadcasting Updates

```python
def broadcast_task_update(task):
    """Broadcast task update to all connected clients"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'project_{task.project.id}',
        {
            'type': 'task_update',
            'task': TaskSerializer(task).data
        }
    )
```

### Connection Management
- Auto-reconnect on connection drop
- Heartbeat/ping every 30 seconds
- Connection pooling via Redis
- Graceful degradation to polling if WebSocket unavailable

---

## WIZARDS SYSTEM

### Overview
Guided workflows for complex operations requiring multiple steps.

### Wizard Types

#### 1. Project Creation Wizard
- Step 1: Client selection or creation
- Step 2: Project details
- Step 3: Budget & timeline
- Step 4: Initial team assignment
- Step 5: Schedule template selection
- Step 6: Review & create

#### 2. Invoice Creation Wizard
- Step 1: Select project & date range
- Step 2: Auto-populate line items from completed tasks
- Step 3: Add additional charges
- Step 4: Set payment terms
- Step 5: Review & send

#### 3. Change Order Wizard
- Step 1: Describe change
- Step 2: Select affected tasks/materials
- Step 3: Calculate cost impact
- Step 4: Upload supporting photos
- Step 5: Submit for client approval

### Implementation Pattern

```python
class WizardStep(models.Model):
    wizard_session = ForeignKey('WizardSession', on_delete=CASCADE)
    step_number = IntegerField()
    step_name = CharField(max_length=100)
    data = JSONField(default=dict)
    is_complete = BooleanField(default=False)
    completed_at = DateTimeField(null=True)

class WizardSession(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    wizard_type = CharField(max_length=100)
    current_step = IntegerField(default=1)
    is_complete = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    
    def advance_step(self):
        self.current_step += 1
        self.save()
    
    def complete_wizard(self):
        # Execute final action based on wizard_type
        if self.wizard_type == 'project_creation':
            return self._create_project()
        elif self.wizard_type == 'invoice_creation':
            return self._create_invoice()
```

---

## STRATEGIC PLANNER

### Overview
Long-term planning with schedule weight, progress tracking, and AI-assisted optimization.

### Key Features

#### Schedule Weight
```python
class Task(models.Model):
    schedule_weight = IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Priority weight for visual planner (0-100)'
    )
```

Used for:
- Visual sizing in Kanban boards
- Priority sorting
- Resource allocation decisions
- Critical path calculation

#### Progress Tracking
```python
class Task(models.Model):
    progress_percent = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    checklist = JSONField(default=list, blank=True)
    # Format: [{'item': 'Task description', 'checked': false}, ...]
```

#### AI Optimization
- Resource leveling
- Timeline compression analysis
- What-if scenario planning
- Bottleneck identification

---

## SOP SYSTEM

### Overview
Standard Operating Procedures documentation and distribution system.

### Database Schema

```python
class SOP(models.Model):
    title = CharField(max_length=255)
    category = CharField(max_length=100)
    content = TextField()
    version = CharField(max_length=50)
    status = CharField(max_length=50, choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ])
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class SOPAcknowledgment(models.Model):
    sop = ForeignKey(SOP, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    acknowledged_at = DateTimeField(auto_now_add=True)
    signature = TextField(blank=True)  # Base64 signature image
```

### Features
- Version control
- Employee acknowledgment tracking
- Search and retrieval
- Mobile-optimized viewing
- Signature capture

---

## CROSS-REFERENCES

- See **REQUIREMENTS_OVERVIEW.md** for functional requirements
- See **ARCHITECTURE_UNIFIED.md** for system architecture
- See **API_ENDPOINTS_REFERENCE.md** for complete API documentation
- See **ROLE_PERMISSIONS_REFERENCE.md** for permission details
- See **CALENDAR_COMPLETE_GUIDE.md** for calendar deep-dive

---

**Document Control:**
- Version: 1.0
- Status: Official Master Document #3 of 9
- Owner Approved: December 8, 2025
- Last Updated: December 8, 2025
