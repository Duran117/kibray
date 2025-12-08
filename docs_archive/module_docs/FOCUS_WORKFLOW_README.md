# Executive Focus Workflow - Module 25 (Productivity)

## 📋 Overview

The **Executive Focus Workflow** is a sophisticated daily planning system that combines two proven productivity methodologies:

1. **Pareto Principle (80/20 Rule)**: Identify the critical 20% of tasks that produce 80% of results
2. **Eat That Frog**: Tackle your hardest, most important task first thing in the morning

This system helps executives and project managers prioritize effectively, maintain focus, and sync their tasks with external calendars (Apple Calendar, Google Calendar) via iCal.

---

## 🎯 Key Features

### 1. **4-Step Daily Planning Wizard**
A guided, interactive process that transforms chaos into clarity:

#### **Step 1: Brain Dump** 🧠
- Write down every task on your mind (one per line)
- Self-assess your energy level (1-10 scale)
- No filtering yet - just capture everything

#### **Step 2: The 80/20 Filter** ⚡
- Drag-and-drop tasks to "High Impact" column
- Force yourself to identify which tasks truly matter
- Requires you to explain **WHY** each high-impact task matters
- Prevents superficial prioritization

#### **Step 3: The Frog** 🐸
- Choose THE single most important/hardest task
- Only one Frog allowed per day
- Must be a high-impact task
- This is what you'll tackle first

#### **Step 4: Battle Plan** 🗺️
- Break down your Frog into micro-actions (checklist)
- Time-block when you'll work on it
- Add session notes/reflections

### 2. **Smart Data Models**

#### `DailyFocusSession`
```python
- user: ForeignKey (who's planning)
- date: DateField (which day)
- energy_level: Integer (1-10 self-assessment)
- notes: TextField (reflections, insights)
```

**Automatic Properties:**
- `total_tasks`: Count of all tasks
- `completed_tasks`: How many are done
- `high_impact_tasks`: Count of the critical 20%
- `frog_task`: The single most important task

#### `FocusTask`
```python
# Basic Info
- title: CharField
- description: TextField
- order: Integer (for sorting)

# Pareto Principle
- is_high_impact: Boolean (part of the 20%)
- impact_reason: TextField (WHY it matters)

# Eat That Frog
- is_frog: Boolean (THE most important task)

# Battle Plan
- checklist: JSONField (micro-actions)
  Format: [{"text": "Step 1", "done": false}, ...]
  
# Time Blocking
- scheduled_start: DateTime
- scheduled_end: DateTime

# Calendar Integration
- calendar_token: UUID (secure token for iCal)

# Status
- is_completed: Boolean
- completed_at: DateTime
```

**Automatic Properties:**
- `duration_minutes`: Calculated from start/end times
- `checklist_progress`: Percentage (0-100)
- `checklist_completed`: Count of done items
- `checklist_total`: Total checklist items

**Smart Methods:**
- `get_calendar_title()`: "🐸 Task Title" or "⚡ Task Title"
- `get_calendar_description()`: Full formatted description with checklist

### 3. **Data Validation Rules**

The system enforces productivity best practices:

✅ **Energy level must be 1-10**
```python
ValidationError if < 1 or > 10
```

✅ **Only ONE Frog per session**
```python
# Prevents:
session.focus_tasks.filter(is_frog=True).count() > 1
```

✅ **Frog must be high-impact**
```python
# Ensures your #1 task is actually important
if is_frog and not is_high_impact:
    raise ValidationError
```

✅ **High-impact requires reason**
```python
# Forces you to articulate WHY
if is_high_impact and not impact_reason.strip():
    raise ValidationError
```

✅ **Valid time blocks**
```python
if scheduled_end <= scheduled_start:
    raise ValidationError
```

---

## 🔌 REST API

### Authentication
All endpoints require authentication:
```python
from rest_framework.permissions import IsAuthenticated
```

### Endpoints

#### **DailyFocusSessionViewSet**

**List/Create Sessions**
```http
GET/POST /api/v1/focus/sessions/
```

**Create with tasks:**
```json
{
  "date": "2025-11-29",
  "energy_level": 8,
  "notes": "Feeling productive!",
  "tasks": [
    {
      "title": "Complete project proposal",
      "is_high_impact": true,
      "impact_reason": "Will bring $50K revenue",
      "is_frog": true,
      "checklist": [
        {"text": "Research requirements", "done": false},
        {"text": "Write draft", "done": false}
      ],
      "scheduled_start": "2025-11-29T09:00:00Z",
      "scheduled_end": "2025-11-29T11:00:00Z"
    }
  ]
}
```

**Get Today's Session**
```http
GET /api/v1/focus/sessions/today/
```

**Get This Week's Sessions**
```http
GET /api/v1/focus/sessions/this_week/
```

**Complete a Task**
```http
POST /api/v1/focus/sessions/{id}/complete_task/
Body: {"task_id": 123}
```

**Update Checklist**
```http
POST /api/v1/focus/sessions/{id}/update_checklist/
Body: {
  "task_id": 123,
  "checklist": [
    {"text": "Step 1", "done": true},
    {"text": "Step 2", "done": false}
  ]
}
```

#### **FocusTaskViewSet**

**List/Create/Update/Delete Tasks**
```http
GET/POST/PATCH/DELETE /api/v1/focus/tasks/
```

**Get Upcoming Tasks (Next 7 Days)**
```http
GET /api/v1/focus/tasks/upcoming/
```

**Get Frog History**
```http
GET /api/v1/focus/tasks/frog_history/?days=30
```

**Toggle Task Completion**
```http
PATCH /api/v1/focus/tasks/{id}/toggle_complete/
```

**Update Time Block**
```http
PATCH /api/v1/focus/tasks/{id}/update_time_block/
Body: {
  "scheduled_start": "2025-11-29T09:00:00Z",
  "scheduled_end": "2025-11-29T11:00:00Z"
}
```

#### **Stats Endpoint**

**Get Productivity Statistics**
```http
GET /api/v1/focus/stats/?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "total_sessions": 20,
  "total_tasks": 85,
  "completed_tasks": 68,
  "completion_rate": 80.0,
  "total_frogs": 20,
  "completed_frogs": 18,
  "frog_completion_rate": 90.0,
  "high_impact_tasks": 45,
  "avg_energy_level": 7.2
}
```

---

## 📅 External Calendar Sync (iCal)

### How It Works

The system generates **iCalendar (.ics) feeds** that can be subscribed to in any calendar app:

1. User completes the wizard
2. Tasks with scheduled times are included in the feed
3. Calendar apps poll the feed URL for updates
4. Changes sync automatically

### Feed URLs

**Focus Tasks Only:**
```
webcal://your-domain.com/api/calendar/feed/<user_token>.ics
```

**Master Calendar (Focus + Projects + Invoices):**
```
webcal://your-domain.com/api/calendar/master/<user_token>.ics
```

### Subscribing to Calendar

#### **Apple Calendar (macOS/iOS)**
1. Click "Subscribe to Calendar" button in wizard
2. Copy the `webcal://` URL
3. Open Calendar app
4. File → New Calendar Subscription
5. Paste URL → Subscribe
6. Choose refresh interval (15 minutes recommended)

#### **Google Calendar**
1. Copy the `webcal://` URL
2. Replace `webcal://` with `https://`
3. Open Google Calendar settings
4. "Add calendar" → "From URL"
5. Paste URL → Add calendar

### Event Formatting

**Frog Tasks (🐸):**
- Summary: `🐸 Task Title`
- Priority: 1 (Highest)
- Categories: `["Frog"]`
- Color: Green
- Alarm: 15 minutes before

**High Impact Tasks (⚡):**
- Summary: `⚡ Task Title`
- Priority: 5 (Medium)
- Categories: `["High Impact"]`
- Color: Orange

**Regular Tasks:**
- Summary: `Task Title`
- Priority: 9 (Low)

**Event Description Includes:**
- Task description
- Impact reason (if high-impact)
- Complete checklist with status checkboxes
- Methodology tags

**Example:**
```
🐸 Complete Q1 Proposal

This is the detailed description of the task.

🐸 EAT THAT FROG - Most Important Task of the Day
⚡ HIGH IMPACT - Part of the Critical 20%

💡 Why it matters: Will bring in $50K revenue for Q1

✓ Battle Plan:
⬜ 1. Research client requirements
⬜ 2. Draft executive summary
⬜ 3. Get approval from team
```

---

## 🎨 Frontend Wizard

### URL
```
/focus/
```

### Features

**Responsive Design:**
- Desktop: Full wizard with drag-and-drop
- Mobile: Touch-friendly interface
- Tablet: Optimized layout

**Step Navigation:**
- Progress indicator with completed checkmarks
- Previous/Next buttons
- Validation before advancing

**Energy Selector:**
- Visual 1-10 button grid
- Hover effects
- Selected state styling

**Drag & Drop (Step 2):**
- Smooth animations
- Visual feedback on hover
- Columns: "All Tasks" ↔ "High Impact"

**Frog Selection (Step 3):**
- Radio-style selection
- Shows impact reason for context
- Visual highlighting

**Battle Plan Builder (Step 4):**
- Dynamic checklist with add/remove
- DateTime picker for time blocking
- Real-time duration calculation
- Session notes textarea

**Success Page:**
- Calendar subscription instructions
- One-click URL copy
- Links to Dashboard and Master Schedule

### Styling
- **Tailwind CSS** for utility classes
- **Custom CSS** for wizard-specific components
- **Animations**: fadeIn, scale transforms
- **Color Palette**: Purple gradient headers, semantic colors

---

## 🔐 Security & Permissions

### Authentication Required
All views and API endpoints require login:
```python
@login_required
@permission_classes([IsAuthenticated])
```

### User Data Isolation
Users can only see/edit their own data:
```python
queryset.filter(session__user=request.user)
```

### Calendar Token Security
⚠️ **Current Implementation:**
- Uses `user.id` as token (simple but not secure)

🔒 **Recommended Enhancement:**
```python
# Add to User Profile model:
calendar_feed_token = models.UUIDField(
    default=uuid.uuid4,
    unique=True,
    editable=False
)
```

Then update feed URLs:
```python
/api/calendar/feed/<uuid:calendar_feed_token>.ics
```

---

## 📊 Django Admin

### DailyFocusSession Admin

**List View:**
- Date, User, Energy Level
- Total Tasks / Completed Tasks (with %)
- Frog Task preview
- Sortable by date, energy level

**Edit View:**
- Session info fieldset
- Notes (collapsible)
- Inline task editing
- Metadata (read-only)

### FocusTask Admin

**List View:**
- Title with emoji (🐸/⚡)
- Session User & Date
- High Impact / Frog flags
- Completion status
- Scheduled time & duration

**Edit View:**
- Task info
- Pareto & Frog section
- Battle Plan (checklist)
- Time Blocking
- Status & completion tracking
- Calendar integration details

**Filters:**
- is_high_impact
- is_frog
- is_completed
- session__date
- session__user

---

## 🧪 Testing

### Test Coverage: 14/14 (100%)

**Model Tests:**
- ✅ Create daily focus session
- ✅ Energy level validation (1-10)
- ✅ Create focus task with all fields
- ✅ Only one Frog per session validation
- ✅ Frog must be high-impact validation
- ✅ High-impact requires reason validation
- ✅ Calendar title formatting (emojis)

**API Tests:**
- ✅ Create session via API with tasks
- ✅ Get today's session
- ✅ Focus stats endpoint

**View Tests:**
- ✅ Wizard requires login
- ✅ Wizard renders correctly

**Calendar Tests:**
- ✅ iCal feed generates
- ✅ Invalid token returns 404

### Run Tests
```bash
pytest tests/test_focus_workflow.py -v
```

---

## 🚀 Usage Examples

### Example 1: Morning Planning Routine

**7:00 AM - Start Wizard**
```
Energy Level: 8/10
Brain Dump:
- Review project proposal
- Call supplier about materials
- Update team on progress
- Fix bug in production
- Review timesheets
- Plan next week's schedule
```

**Step 2: Identify High Impact**
Drag to High Impact:
- ✅ Review project proposal
  - Why: Client meeting at 2 PM, need to be prepared
- ✅ Fix bug in production
  - Why: Blocking 5 users from completing work

**Step 3: Choose Frog**
🐸 **Fix bug in production**
(It's harder and more urgent than proposal review)

**Step 4: Battle Plan**
Checklist:
- [ ] Reproduce bug locally
- [ ] Review error logs
- [ ] Identify root cause
- [ ] Write fix
- [ ] Test fix
- [ ] Deploy to production

Time Block: 9:00 AM - 11:00 AM

**Result:**
- Crystal clear priorities
- Bug fixed by 11 AM ✅
- Rest of day flows smoothly

### Example 2: API Integration

**Create Session Programmatically:**
```python
import requests

response = requests.post(
    'https://your-domain.com/api/v1/focus/sessions/',
    headers={'Authorization': 'Bearer YOUR_JWT_TOKEN'},
    json={
        'date': '2025-11-29',
        'energy_level': 7,
        'notes': 'Let\'s crush it today!',
        'tasks': [
            {
                'title': 'Complete client proposal',
                'is_high_impact': True,
                'impact_reason': '$50K deal on the line',
                'is_frog': True,
                'scheduled_start': '2025-11-29T09:00:00Z',
                'scheduled_end': '2025-11-29T11:00:00Z',
                'checklist': [
                    {'text': 'Review requirements', 'done': False},
                    {'text': 'Write executive summary', 'done': False},
                    {'text': 'Get team approval', 'done': False}
                ]
            }
        ]
    }
)

print(response.json())
```

### Example 3: Track Your Stats

**Get 30-Day Performance:**
```python
response = requests.get(
    'https://your-domain.com/api/v1/focus/stats/?days=30',
    headers={'Authorization': 'Bearer YOUR_JWT_TOKEN'}
)

stats = response.json()
print(f"You completed {stats['frog_completion_rate']}% of your Frogs!")
print(f"Average energy: {stats['avg_energy_level']}/10")
```

---

## 🔄 Integration with Master Schedule

The Focus Workflow integrates seamlessly with the Master Schedule Center:

1. **Calendar View**: Focus tasks appear alongside projects and invoices
2. **Unified Feed**: `/api/calendar/master/<token>.ics` includes everything
3. **Cross-linking**: Success page links to Master Schedule

---

## 🎓 Methodology Background

### Pareto Principle (80/20 Rule)
- Discovered by economist Vilfredo Pareto
- 80% of effects come from 20% of causes
- Applied to productivity: 20% of tasks produce 80% of results
- **Our implementation**: Forces you to identify that critical 20%

### Eat That Frog
- From Brian Tracy's book "Eat That Frog!"
- "Frog" = your biggest, most important task
- Do it first thing in the morning
- Everything else becomes easier
- **Our implementation**: One Frog per day, time-blocked early

### Time Blocking
- Cal Newport's "Deep Work" methodology
- Schedule specific times for important work
- Prevents reactive, distracted workdays
- **Our implementation**: DateTime picker with duration calculation

---

## 📈 Future Enhancements

### Planned Features

**1. Secure Calendar Tokens**
- Replace user.id with UUID tokens
- Regenerate token functionality
- Token expiration support

**2. Timezone Support**
- Pull timezone from user profile
- Convert all times to user's timezone
- Handle DST transitions

**3. Streak Tracking**
- Track consecutive days of Frog completion
- Gamification badges
- Weekly/monthly performance charts

**4. Weekly Review Dashboard**
- Summary of week's accomplishments
- Energy level trends
- High-impact task analysis
- Suggestions for improvement

**5. AI-Powered Insights**
- Suggest which tasks should be Frogs
- Predict optimal time blocks based on history
- Energy level pattern recognition

**6. Team Features**
- Share Frog tasks with manager
- Team Frog visibility (optional)
- Collaborative high-impact task identification

**7. Mobile App**
- Native iOS/Android apps
- Push notifications for Frog reminders
- Quick task completion checkboxes

---

## 🛠️ Technical Stack

- **Backend**: Django 5.0+
- **API**: Django REST Framework
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **Calendar**: icalendar 6.1.0
- **Database**: PostgreSQL (JSONField for checklists)
- **Authentication**: JWT tokens

---

## 📝 Database Schema

```sql
-- DailyFocusSession
CREATE TABLE core_dailyfocussession (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    date DATE NOT NULL,
    energy_level INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, date)
);

-- FocusTask
CREATE TABLE core_focustask (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES core_dailyfocussession(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_high_impact BOOLEAN DEFAULT FALSE,
    impact_reason TEXT,
    is_frog BOOLEAN DEFAULT FALSE,
    checklist JSONB,
    scheduled_start TIMESTAMP WITH TIME ZONE,
    scheduled_end TIMESTAMP WITH TIME ZONE,
    calendar_token UUID UNIQUE,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

---

## 🤝 Contributing

When extending this module:

1. **Maintain Validation Rules**: Don't compromise on the constraints
2. **Keep UI Simple**: The wizard should be intuitive, not overwhelming
3. **Test Coverage**: Add tests for any new features
4. **Document API Changes**: Update this README

---

## 📞 Support

For questions or issues:
- Check test file: `tests/test_focus_workflow.py`
- Review API serializers: `core/api/serializers.py`
- Inspect models: `core/models.py` (search for "Focus Workflow")

---

## ✅ Checklist for Deployment

- [x] Models created and migrated
- [x] API endpoints implemented
- [x] Frontend wizard built
- [x] Calendar feed working
- [x] Admin interface configured
- [x] Tests passing (14/14)
- [ ] Secure calendar tokens (user.id → UUID)
- [ ] Timezone handling from profile
- [ ] Production calendar feed URL (webcal://)
- [ ] SSL certificate for calendar sync
- [ ] Rate limiting on calendar feed
- [ ] Monitoring for feed errors

---

**Built with 🐸 by the Kibray Team**

*"Eat that frog! If you have to eat two frogs, eat the ugliest one first."* - Brian Tracy
