# Kibray User Guide

## Welcome to Kibray!

Kibray is a comprehensive construction project management platform with Progressive Web App (PWA) capabilities.

## Table of Contents

1. [Getting Started](#getting-started)
2. [PWA Features](#pwa-features)
3. [Project Management](#project-management)
4. [Time Tracking](#time-tracking)
5. [Financial Management](#financial-management)
6. [Communication](#communication)
7. [Mobile Features](#mobile-features)
8. [Offline Mode](#offline-mode)
9. [Notifications](#notifications)
10. [Tips & Tricks](#tips--tricks)

## Getting Started

### Creating an Account

1. Navigate to https://kibray.com
2. Click **Sign Up**
3. Enter your details:
   - Email address
   - Username
   - Password (min 8 characters)
4. Verify your email
5. Complete your profile

### First Login

1. Go to https://kibray.com
2. Enter username and password
3. (Optional) Enable Two-Factor Authentication for security
4. You'll see your Dashboard

## PWA Features

### Installing Kibray as an App

#### On Android (Chrome/Edge)

1. Visit https://kibray.com in Chrome
2. Look for **"Install Kibray"** banner at bottom
3. Tap **Install**
4. App will appear on your home screen
5. Launch like a native app!

Or manually:
1. Tap the **⋮** menu (top-right)
2. Select **"Add to Home screen"**
3. Confirm installation

#### On iOS (Safari)

1. Visit https://kibray.com in Safari
2. Look for **iOS Install Prompt** popup
3. Follow instructions:
   - Tap the **Share** button (⎗)
   - Scroll down and tap **"Add to Home Screen"**
   - Tap **"Add"**
4. App will appear on your home screen

#### On Desktop (Chrome/Edge)

1. Visit https://kibray.com in Chrome or Edge
2. Look for **install icon** (⊕) in address bar
3. Click **Install**
4. Kibray opens in its own window

### Benefits of Installing

- **Faster Loading**: Cached for instant access
- **Offline Access**: Work without internet
- **Full Screen**: No browser UI clutter
- **Home Screen Icon**: Launch like any app
- **Push Notifications**: Never miss updates
- **Background Sync**: Auto-sync when online

## Project Management

### Creating a Project

1. Go to **Projects** → **New Project**
2. Fill in details:
   - **Project Name**: e.g., "Downtown Office Renovation"
   - **Client**: Select or create new
   - **Start Date** / **End Date**
   - **Budget**: Labor + Materials
   - **Description**: Project scope
3. Click **Create Project**

### Managing Tasks

#### Create Task

1. Open project
2. Click **Tasks** → **Add Task**
3. Enter:
   - **Title**: Task name
   - **Description**: Details
   - **Assigned To**: Team member
   - **Due Date**: Deadline
   - **Priority**: Low/Medium/High/Critical
   - **Status**: Pending/In Progress/Completed
4. Save

#### Update Task Status

**Drag & Drop (Kanban)**:
- Drag task card to different column
- Columns: Pending → In Progress → Completed

**Quick Update**:
- Click task → Change status dropdown
- Or use **Bulk Update** for multiple tasks

#### Task Attachments

- Click task → **Attachments** tab
- Drag & drop photos
- Or click **Upload** button
- Supports: JPG, PNG, PDF (max 10MB)

### Gantt Chart

View project timeline:

1. Open project → **Schedule** tab
2. Switch to **Gantt Chart** view
3. Features:
   - Drag bars to adjust dates
   - Click task to edit
   - Dependencies shown with arrows
   - Critical path highlighted in red

## Time Tracking

### Logging Time

#### Quick Entry

1. Click **⏱ Log Time** (top bar)
2. Select:
   - **Project**
   - **Date**
   - **Hours Worked**
   - **Description** (what you did)
3. Save

#### Timer Mode

1. Click **Start Timer** on project
2. Work on task
3. Click **Stop Timer**
4. Auto-creates time entry

### Viewing Time Reports

1. Go to **Reports** → **Time Tracking**
2. Filters:
   - Date range
   - Project
   - Employee
3. Export to:
   - **PDF** (for invoicing)
   - **CSV** (for Excel/Google Sheets)

## Financial Management

### Creating Invoices

1. Go to **Finance** → **Invoices** → **New Invoice**
2. Select project
3. Add line items:
   - Labor hours (auto-filled from time entries)
   - Materials
   - Equipment rental
4. Review totals:
   - Subtotal
   - Tax (auto-calculated)
   - Total
5. Click **Generate Invoice**
6. **Send to Client**:
   - Email directly from Kibray
   - Or download PDF

### Tracking Expenses

1. **Finance** → **Expenses** → **Add Expense**
2. Enter:
   - **Date**: When incurred
   - **Project**: Related project
   - **Category**: Materials/Labor/Equipment
   - **Amount**: Cost
   - **Receipt**: Upload photo
3. Save

### Budget vs Actual

View financial health:

1. Open project → **Financial** tab
2. See:
   - **Budget**: Original estimate
   - **Actual**: Spent to date
   - **Variance**: Over/Under budget
   - **% Complete**: Budget utilization
3. Charts:
   - Budget breakdown (pie chart)
   - Spending over time (line chart)
   - Earned Value Analysis

## Communication

### Team Chat

#### Send Message

1. Click **💬 Chat** (sidebar)
2. Select channel or person
3. Type message
4. Press **Enter** or click **Send**

#### Features

- **@mentions**: @username to notify
- **#channels**: #project-name for channels
- **File sharing**: Drag & drop files
- **Emoji reactions**: React to messages
- **Message search**: 🔍 Search bar at top

### Notifications

View all notifications:

1. Click **🔔** (top-right)
2. See:
   - New messages
   - Task assignments
   - Status updates
   - @mentions
3. Click notification to jump to item

#### Notification Settings

1. Click **Profile** → **Settings** → **Notifications**
2. Toggle on/off for each type:
   - Email notifications
   - Push notifications
   - In-app notifications
3. Set **Quiet Hours**: No notifications during these times

## Mobile Features

### Pull to Refresh

On mobile:
1. Swipe down on any list (projects, tasks, etc.)
2. Release to refresh
3. See latest data

### Haptic Feedback

Vibration on:
- Task completion (light vibration)
- Error (double vibration)
- Important notification (strong vibration)

### Share API

Share projects/tasks:
1. Open item → **⋯** menu
2. Click **Share**
3. Choose app (Messages, Email, Slack, etc.)

### Voice Input

Use voice to add tasks:
1. Tap microphone icon in task title field
2. Speak: "Inspect electrical panel in unit 5"
3. Tap **Done**

## Offline Mode

### What Works Offline

✅ **Available**:
- View projects you've opened before
- View tasks and details
- Create new tasks (synced later)
- Update task status
- Add time entries
- View schedules
- Read messages

❌ **Requires Internet**:
- Upload photos/files
- Generate invoices
- Send email notifications
- Real-time chat

### Offline Indicator

When offline:
- **Orange banner** appears at top: "You're offline. Changes will sync when reconnected."
- **Cloud icon** turns gray

### Automatic Sync

When you reconnect:
1. Changes automatically upload
2. You'll see: "✅ Synced 3 changes"
3. If conflicts: Notification to resolve

### Manual Sync

Force sync:
1. Pull down on any page (pull-to-refresh)
2. Or click **⟳ Sync** button

## Notifications

### Push Notifications

#### Enable on Desktop

1. First visit: Click **"Allow"** when prompted
2. Or go to **Settings** → **Notifications**
3. Click **Enable Push Notifications**
4. Browser will ask for permission → Allow

#### Enable on Mobile

**Android**:
- Automatically prompted after install
- Or: **Settings** → **Notifications** → Toggle on

**iOS** (if installed as PWA):
- **Settings** → **Notifications**
- Find **Kibray**
- Toggle **Allow Notifications**

### Notification Types

- **Task Assigned**: When someone assigns you a task
- **Task Due Soon**: 24 hours before deadline
- **Task Overdue**: Daily reminder for overdue tasks
- **Message Received**: New chat message
- **@Mention**: Someone mentioned you
- **Status Change**: Task/project status changed
- **Payment Received**: Invoice paid
- **Budget Alert**: Project over budget

### Customizing Notifications

1. **Profile** → **Settings** → **Notifications**
2. Toggle each type on/off
3. Set preferences:
   - **Instant**: Real-time push
   - **Daily Digest**: Once per day summary
   - **Off**: No notifications

## Tips & Tricks

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `N` | New Project/Task |
| `/` | Focus search bar |
| `Esc` | Close modal/dialog |
| `Ctrl+S` | Save form |
| `Ctrl+K` | Command palette |

### Quick Actions

- **Right-click** on task → Context menu with quick actions
- **Double-click** on project → Open project detail
- **Drag & drop** files anywhere → Upload

### Filters & Search

**Global Search** (`/`):
- Search across projects, tasks, clients
- Type: "project:renovation" to filter by project
- Type: "status:pending" to filter by status
- Type: "@john" to find John's tasks

**Save Filters**:
1. Apply filters (e.g., status=pending, priority=high)
2. Click **Save Filter** → Name it "Urgent Tasks"
3. Access from sidebar under **Saved Filters**

### Bulk Operations

Select multiple items:
1. Check boxes next to tasks
2. Click **Bulk Actions** dropdown
3. Choose:
   - Change Status
   - Assign To
   - Set Priority
   - Delete

### Keyboard Navigation

- `Tab` → Move between form fields
- `Arrow keys` → Navigate lists
- `Enter` → Open selected item
- `Space` → Toggle checkbox

### Dark Mode

1. **Profile** → **Settings** → **Appearance**
2. Select theme:
   - **Light**: Default
   - **Dark**: Dark mode
   - **Auto**: Matches system setting

### Export Data

Export your data:

1. **Settings** → **Data & Privacy** → **Export Data**
2. Choose format:
   - **JSON**: All data, machine-readable
   - **CSV**: Spreadsheet format
   - **PDF**: Human-readable reports
3. Click **Request Export**
4. Receive download link via email (may take a few minutes)

### Calendar Integration

Sync with your calendar:

1. Go to **Schedule** → **Settings**
2. Copy **iCal Feed URL**
3. Add to your calendar app:
   - **Google Calendar**: Add by URL
   - **Apple Calendar**: File → New Calendar Subscription
   - **Outlook**: Add Calendar → From Internet
4. Tasks/schedules auto-sync

### Browser Compatibility

Recommended browsers:
- ✅ **Chrome** 90+ (best performance)
- ✅ **Edge** 90+
- ✅ **Safari** 14+ (iOS/macOS)
- ✅ **Firefox** 88+
- ⚠️ **Internet Explorer**: Not supported

## Troubleshooting

### App Won't Install

**Android/Desktop**:
- Ensure you're on HTTPS
- Clear browser cache
- Try Chrome/Edge

**iOS**:
- Must use Safari (not Chrome)
- iOS 11.3+ required

### Notifications Not Working

1. Check browser/OS permissions:
   - **Chrome**: Settings → Site Settings → Notifications → Allow
   - **iOS**: Settings → Notifications → Safari/Kibray → Allow
2. Check Kibray settings: **Profile** → **Notifications**
3. Try disabling and re-enabling

### Offline Mode Not Working

1. Close and reopen app
2. Check service worker:
   - Chrome DevTools → Application → Service Workers
   - Should show "activated and running"
3. Clear cache and reload

### Sync Conflicts

If changes conflict:
1. You'll see: "⚠️ Sync Conflict"
2. Click **Resolve**
3. Choose:
   - **Use Server Version**: Discard local changes
   - **Use My Version**: Overwrite server
   - **Merge**: Combine both (if possible)

### Performance Issues

- **Clear cache**: Settings → Privacy → Clear Data
- **Reduce animations**: Settings → Accessibility → Reduce Motion
- **Update browser**: Ensure latest version
- **Check internet speed**: Minimum 1 Mbps recommended

## Getting Help

### In-App Help

- Click **?** icon (bottom-right) for contextual help
- Or press `Shift+?` to open help center

### Support Channels

- **Email**: support@kibray.com
- **Chat**: Click **💬 Support** (bottom-right) for live chat
- **Knowledge Base**: https://help.kibray.com
- **Community Forum**: https://community.kibray.com

### Reporting Bugs

1. Click **Profile** → **Help** → **Report Bug**
2. Describe issue:
   - What you were doing
   - What happened
   - What you expected
3. Auto-includes:
   - Browser/OS version
   - Error logs
   - Screenshot (optional)
4. Submit

### Feature Requests

1. Go to https://feedback.kibray.com
2. Click **Submit Idea**
3. Describe feature and use case
4. Vote on others' requests
5. Track status of your request

## Conclusion

Congratulations! You now know how to use Kibray's key features.

### Next Steps

1. ✅ Install PWA on your devices
2. ✅ Enable push notifications
3. ✅ Create your first project
4. ✅ Invite team members
5. ✅ Explore mobile features
6. ✅ Set up calendar sync

**Welcome to productive project management! 🚀**

---

**Need more help?** Contact support@kibray.com or visit https://help.kibray.com
