# CALENDAR COMPLETE GUIDE
**System:** Kibray ERP  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Calendar Views](#calendar-views)
4. [Role-Based Visibility](#role-based-visibility)
5. [AI Integration](#ai-integration)
6. [External Calendar Sync](#external-calendar-sync)
7. [Drag & Drop](#drag--drop)
8. [Conflict Detection](#conflict-detection)
9. [User Guide](#user-guide)
10. [API Integration](#api-integration)

---

## SYSTEM OVERVIEW

The Kibray Calendar System is a **modular, role-based, AI-powered scheduling platform** providing unified visibility across projects, tasks, and resources with intelligent conflict detection and external calendar integration.

### Key Features
- ✅ Multiple view types (Timeline, Daily, Weekly, Monthly)
- ✅ Role-layered visibility
- ✅ AI-powered insights and recommendations
- ✅ Bidirectional sync with Apple Calendar & Google Calendar
- ✅ Drag & drop scheduling (PM/Admin only)
- ✅ Real-time conflict detection
- ✅ Client-appropriate visibility
- ✅ WebSocket real-time updates

---

## ARCHITECTURE

### Modular Design

```
┌─────────────────────────────────────┐
│      BASE CALENDAR ENGINE           │
│  (Core scheduling & event storage)  │
└───────────┬─────────────────────────┘
            │
    ┌───────┴────────┬────────┬────────┐
    │                │        │        │
┌───▼────┐  ┌───────▼───┐ ┌──▼────┐ ┌─▼────┐
│ ADMIN  │  │    PM     │ │ EMPL  │ │CLIENT│
│ LAYER  │  │  LAYER    │ │ LAYER │ │LAYER │
└────────┘  └───────────┘ └───────┘ └──────┘
    │            │            │         │
    └────────────┴────────────┴─────────┘
                 │
         ┌───────▼────────┐
         │   AI LAYER     │
         │ (Insights &    │
         │ Recommendations)│
         └────────────────┘
```

### Technology Stack
- **Backend:** Django with Celery for async operations
- **Database:** PostgreSQL with optimized indexes
- **Cache:** Redis for performance
- **Real-time:** Django Channels (WebSocket)
- **External Sync:** Google Calendar API, Apple Calendar API
- **Frontend:** Vue.js with drag-drop library

---

## CALENDAR VIEWS

### 1. Timeline View (Gantt-Style)

**Purpose:** Visualize project timeline with dependencies and critical path

**Features:**
- Projects/phases as rows
- Time as columns (configurable: days, weeks, months)
- Drag & drop to reschedule (PM/Admin only)
- Dependency lines connecting related tasks
- Critical path highlighting
- Milestone markers
- Resource allocation bars

**Use Cases:**
- High-level project planning
- Identifying bottlenecks
- Managing dependencies
- Communicating timeline to stakeholders

**Implementation:**
```javascript
// Vue.js Timeline Component
<TimelineView
  :projects="projects"
  :events="events"
  :dependencies="dependencies"
  :editable="canEdit"
  @event-moved="handleEventMove"
/>
```

---

### 2. Daily View

**Purpose:** Detailed view of today's schedule

**Features:**
- Hour-by-hour breakdown
- Employee assignments
- Task priorities
- Weather alerts (for outdoor work)
- Quick status updates
- Check-in/check-out tracking

**Layout:**
```
┌─────────────────────────────────────┐
│  Today: December 8, 2025            │
├─────────────────────────────────────┤
│  08:00 AM                           │
│  ┌─────────────────────────────┐   │
│  │ Foundation Pour - Site A    │   │
│  │ Assigned: John, Mike        │   │
│  │ Status: In Progress ●       │   │
│  └─────────────────────────────┘   │
│                                     │
│  10:00 AM                           │
│  ┌─────────────────────────────┐   │
│  │ Client Meeting - Site B     │   │
│  │ PM: Jane Smith              │   │
│  │ Client: Bob Johnson         │   │
│  └─────────────────────────────┘   │
│                                     │
│  02:00 PM                           │
│  ┌─────────────────────────────┐   │
│  │ Paint Interior - Site C     │   │
│  │ Assigned: Sarah, Tom        │   │
│  │ ⚠️  Weather Risk            │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

### 3. Weekly View

**Purpose:** Week-at-a-glance for capacity planning

**Features:**
- 7-day grid
- Resource allocation visualization
- Over-allocation warnings
- Drag & drop to reschedule
- Capacity heatmap
- Conflict indicators

**Colors:**
- 🟢 Green: Under-allocated
- 🟡 Yellow: Optimally allocated
- 🔴 Red: Over-allocated

---

### 4. Monthly View

**Purpose:** High-level overview and milestone tracking

**Features:**
- Calendar grid (traditional month view)
- Milestone markers
- Phase boundaries
- Project start/end dates
- Capacity trends
- Quick navigation

**Interaction:**
- Click day to see detail
- Hover for quick info
- Drag events between days (PM/Admin)

---

### 5. Expandable Task Blocks

**Purpose:** Quick access to task details without leaving calendar

**Features:**
- Click to expand inline
- View full description, notes, photos
- Update status and progress
- Add comments
- Upload photos
- Log time

**Implementation:**
```javascript
<CalendarEvent
  :event="event"
  :expandable="true"
  @expand="showDetails"
  @quick-edit="handleQuickEdit"
/>
```

---

### 6. AI Insights Layer

**Purpose:** Proactive intelligence overlay on calendar

**Visual Indicators:**
- 🔴 Critical risk
- 🟡 Moderate risk
- 🔵 Optimization opportunity
- ⚡ Conflict detected
- 🌤️ Weather impact

**AI Detects:**
- Schedule conflicts
- Resource over-allocation
- Weather risks
- Dependency violations
- Illogical date sequences
- Missing tasks
- Budget constraints

---

## ROLE-BASED VISIBILITY

### Admin View
**Sees:** Everything across all projects
- All calendar events
- All projects
- All employees
- Internal notes
- Financial data indicators
- Full AI insights

### PM View
**Sees:** Only assigned projects
- Events for their projects
- Their team assignments
- Client-facing events
- AI insights for their projects
- Budget alerts for their projects

**Restrictions:**
- Cannot see other PM projects
- Cannot see company-wide analytics

### Employee View
**Sees:** Only their assigned tasks
- Their daily schedule
- Task details
- Instructions
- SOPs
- Check-in/out

**Restrictions:**
- No project overview
- No other employees' schedules
- No financial data
- No client information

### Client View
**Sees:** Project progress and milestones
- Major milestones
- Phase start/end dates
- Scheduled inspections
- Meetings involving them
- Approved progress updates

**Restrictions:**
- No internal team assignments
- No employee names (optional)
- No cost data
- No internal notes
- No other projects

---

## AI INTEGRATION

### Conflict Detection

#### Resource Conflicts
```python
def detect_resource_conflicts(event):
    """Check for employee over-allocation"""
    overlapping = CalendarEvent.objects.filter(
        assigned_to__in=event.assigned_to.all(),
        start_datetime__lt=event.end_datetime,
        end_datetime__gt=event.start_datetime
    ).exclude(id=event.id)
    
    if overlapping.exists():
        return {
            'type': 'resource_conflict',
            'severity': 'high',
            'message': f'{overlapping.count()} overlapping assignments',
            'recommendation': 'Reassign or reschedule'
        }
```

#### Weather Risk Detection
```python
def check_weather_risk(event):
    """Check weather forecast for outdoor work"""
    if not event.project.is_outdoor:
        return None
    
    forecast = weather_api.get_forecast(
        location=event.project.location,
        date=event.start_datetime.date()
    )
    
    if forecast['precipitation_probability'] > 50:
        return {
            'type': 'weather_risk',
            'severity': 'medium',
            'message': f'{forecast["precipitation_probability"]}% chance of rain',
            'recommendation': 'Consider rescheduling outdoor work'
        }
```

#### Dependency Violations
```python
def check_dependencies(event):
    """Verify all dependencies are complete"""
    incomplete = event.dependencies.filter(
        status__ne='completed'
    )
    
    if incomplete.exists():
        return {
            'type': 'dependency_not_met',
            'severity': 'critical',
            'message': f'{incomplete.count()} incomplete dependencies',
            'recommendation': 'Complete dependencies first or update schedule'
        }
```

### AI Recommendations

**Example Recommendations:**
1. "Move 'Foundation Pour' to Tuesday - better weather forecast"
2. "John is over-allocated on Jan 20. Consider assigning Mike instead."
3. "Critical path delayed by 2 days. Recommend adding resources to 'Framing' task."
4. "Budget risk detected. 'Electrical' phase 15% over budget."

---

## EXTERNAL CALENDAR SYNC

### Supported Platforms
1. **Google Calendar** - Full bidirectional sync
2. **Apple Calendar** - Full bidirectional sync

### Sync Architecture

```
┌──────────────┐
│ Kibray Event │
└──────┬───────┘
       │
   ┌───▼────┐
   │ Sync   │
   │ Engine │
   └───┬────┘
       │
   ┌───┴──────────────┐
   │                  │
┌──▼──────────┐  ┌───▼────────────┐
│   Google    │  │  Apple         │
│   Calendar  │  │  Calendar      │
└─────────────┘  └────────────────┘
```

### Bidirectional Sync

**Kibray → External:**
- Event created in Kibray → Syncs to Google/Apple
- Event updated in Kibray → Updates external calendar
- Event deleted in Kibray → Deletes from external

**External → Kibray:**
- Event created externally → Imports to Kibray (if authorized)
- Event updated externally → Updates Kibray event
- Event deleted externally → Marks Kibray event as cancelled

### Conflict Resolution

**Scenario 1: Both modified simultaneously**
```
IF kibray.updated_at > external.updated_at:
    Push Kibray changes to external
ELSE:
    Pull external changes to Kibray
    Notify user of change
```

**Scenario 2: Deleted vs Modified**
```
IF deleted_in_one AND modified_in_other:
    Ask user which to keep
    Present both versions
    Log decision
```

### Sync Frequency
- **Real-time:** Immediate sync on Kibray changes
- **Polling:** Every 5 minutes for external changes
- **On-demand:** Manual sync button

### Configuration

```python
# User settings
class UserCalendarSettings(models.Model):
    user = OneToOneField(User)
    
    # Google Calendar
    google_enabled = BooleanField(default=False)
    google_calendar_id = CharField(max_length=255, blank=True)
    google_token = EncryptedTextField(blank=True)
    
    # Apple Calendar
    apple_enabled = BooleanField(default=False)
    apple_calendar_id = CharField(max_length=255, blank=True)
    apple_token = EncryptedTextField(blank=True)
    
    # Sync options
    sync_direction = CharField(choices=[
        ('both', 'Bidirectional'),
        ('kibray_to_external', 'Kibray → External Only'),
        ('external_to_kibray', 'External → Kibray Only')
    ], default='both')
    
    auto_sync_enabled = BooleanField(default=True)
    sync_interval_minutes = IntegerField(default=5)
```

---

## DRAG & DROP

### Permissions
- **Admin:** Full drag & drop capability
- **PM:** Drag & drop for assigned projects only
- **Others:** View only (no drag & drop)

### Interaction Flow

1. User grabs event block
2. Drags to new date/time
3. Visual feedback (transparent copy follows cursor)
4. Drop on new slot
5. Validation check:
   - Has permission?
   - No conflicts?
   - Dependencies met?
6. If valid:
   - Update event
   - Broadcast via WebSocket
   - Sync to external calendars
7. If invalid:
   - Show error message
   - Snap back to original position

### Implementation

```javascript
// Vue.js drag handler
handleDragEnd(event, newStart, newEnd) {
  // Validate
  if (!this.canEditEvent(event)) {
    this.$notify.error('Permission denied')
    return
  }
  
  // Check conflicts
  const conflicts = this.checkConflicts(event, newStart, newEnd)
  if (conflicts.length > 0) {
    this.$confirm('Conflicts detected. Continue?', conflicts)
      .then(() => this.updateEvent(event, newStart, newEnd))
      .catch(() => this.revertDrag(event))
  } else {
    this.updateEvent(event, newStart, newEnd)
  }
}

async updateEvent(event, newStart, newEnd) {
  await api.patch(`/calendar/events/${event.id}/move/`, {
    start_datetime: newStart,
    end_datetime: newEnd
  })
  
  this.$notify.success('Event rescheduled')
}
```

---

## CONFLICT DETECTION

### Types of Conflicts

#### 1. Resource Conflicts
- Same employee assigned to multiple events at same time
- Equipment double-booked
- PM over-allocated across projects

#### 2. Dependency Conflicts
- Task scheduled before its dependencies complete
- Circular dependencies
- Missing dependencies

#### 3. Weather Conflicts
- Outdoor work scheduled during rain
- Extreme heat/cold warnings
- High wind alerts

#### 4. Budget Conflicts
- Phase scheduled but not funded
- Cost overrun projected
- Payment milestone missed

#### 5. Availability Conflicts
- Employee on vacation
- Equipment under maintenance
- Site access restricted

### Conflict Indicators

**Visual:**
- 🔴 Red border on conflicted events
- ⚡ Lightning bolt icon
- Warning badge with count

**Notifications:**
- In-app alert
- Email to PM
- Dashboard warning

---

## USER GUIDE

### For Project Managers

#### Creating an Event
1. Navigate to Calendar
2. Click date/time or "New Event" button
3. Fill in details:
   - Title
   - Description
   - Date & time
   - Assign employees
   - Link to project
   - Set client visibility
4. Save
5. Event syncs to external calendars

#### Rescheduling (Drag & Drop)
1. Click and hold event block
2. Drag to new position
3. Release
4. Confirm if conflicts detected
5. Event updates everywhere

#### Viewing AI Insights
1. Hover over event with warning icon
2. See detected risks
3. Click "View Recommendation"
4. Take suggested action

### For Employees

#### Viewing Your Schedule
1. Open Calendar (defaults to Daily view)
2. See only your assigned tasks
3. Click task to see details
4. Check-in when starting work
5. Upload photos as you progress
6. Check-out when done

### For Clients

#### Viewing Project Timeline
1. Log into Client Portal
2. Navigate to "My Project"
3. Click "Timeline" tab
4. See milestones and progress
5. Comment on events if needed

---

## API INTEGRATION

### Key Endpoints

**List Events:**
```
GET /api/calendar/events/
  ?project_id=uuid
  &start_date=2025-01-01
  &end_date=2025-01-31
```

**Create Event:**
```
POST /api/calendar/events/
{
  "title": "Foundation Pour",
  "start_datetime": "2025-01-20T08:00:00Z",
  "end_datetime": "2025-01-20T16:00:00Z",
  "project_id": "uuid",
  "assigned_to_ids": ["uuid1", "uuid2"]
}
```

**Move Event (Drag & Drop):**
```
PATCH /api/calendar/events/{id}/move/
{
  "start_datetime": "2025-01-21T08:00:00Z",
  "end_datetime": "2025-01-21T16:00:00Z"
}
```

**Get Conflicts:**
```
GET /api/calendar/conflicts/
  ?project_id=uuid
  &start_date=2025-01-01
  &end_date=2025-01-31
```

**Sync External:**
```
POST /api/calendar/events/{id}/sync/
{
  "sync_to": ["google", "apple"]
}
```

---

## CROSS-REFERENCES

- See **MODULES_SPECIFICATIONS.md** for calendar technical specs
- See **API_ENDPOINTS_REFERENCE.md** for complete API documentation
- See **ROLE_PERMISSIONS_REFERENCE.md** for permission details
- See **REQUIREMENTS_OVERVIEW.md** for calendar requirements

---

**Document Control:**
- Version: 1.0
- Status: Official Master Document #6 of 9
- Owner Approved: December 8, 2025
- Last Updated: December 8, 2025
