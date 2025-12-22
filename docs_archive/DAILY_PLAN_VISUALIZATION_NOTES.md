# Daily Plan Visualization & Timeline Mode - Analysis & Plan

## 1. Current State Analysis

### Models
- **DailyPlan** (`core/models.py`):
    - Represents a plan for a specific project and date.
    - Fields: `project`, `plan_date`, `status`, `weather_data`, `created_by`, `completion_deadline`.
- **PlannedActivity** (`core/models.py`):
    - Represents an activity within a plan.
    - Fields: `daily_plan`, `title`, `description`, `order`, `assigned_employees`, `estimated_hours`, `actual_hours`, `materials_needed`.
    - **Missing**: `parent` (for nesting), `start_time`, `end_time` (for timeline positioning).

### Views
- `daily_planning_dashboard` (`core/views.py`): Lists recent/today's plans.
- `daily_plan_edit` (`core/views.py`): Detail/Edit view for a single plan. Uses standard Django forms/formsets.

### Templates
- `core/daily_planning_dashboard.html`
- `core/daily_plan_edit.html`

## 2. Target Design

### UI Structure
- **Timeline View**:
    - X-Axis: Time (Hours of the day).
    - Y-Axis: Items/Tasks (Hierarchical).
- **Interactions**:
    - Drag & Drop for reordering (Y-axis) and rescheduling (X-axis).
    - Click to open Detail Panel.
    - Zoom controls (Hour/Day view).

### Data Requirements
- Hierarchy: Item -> Task -> Subtask.
    - Need to add `parent` FK to `PlannedActivity`.
- Scheduling:
    - Need `start_time` and `end_time` (or `start_offset` and `duration`) on `PlannedActivity`.
    - Currently only `estimated_hours` exists.

## 3. Implementation Plan

### Phase 1: Backend Updates
1.  Modify `PlannedActivity` model:
    - Add `parent` (ForeignKey to self, null=True).
    - Add `start_time` (TimeField, null=True).
    - Add `end_time` (TimeField, null=True).
2.  Run migrations.
3.  Update `DailyPlanSerializer` (or create a new one) to handle nesting and new fields.
4.  Create API endpoints for:
    - Fetching plan data (nested).
    - Updating activity (move, resize, reorder).
    - Creating activity (with parent).

### Phase 2: Frontend Implementation
1.  Create `core/templates/core/daily_plan_timeline.html`.
2.  Implement Timeline Component:
    - **Header**: Zoom controls, Date navigation.
    - **Sidebar**: List of Items/Tasks (Tree view).
    - **Grid**: Time columns.
    - **Bars**: Absolute positioned divs based on time.
3.  Implement Interactions (JS):
    - Drag & Drop logic.
    - API calls to persist changes.
    - Detail Panel rendering.

### Phase 3: Integration
1.  Add link from `daily_planning_dashboard` to the new Timeline view.
2.  Ensure backward compatibility with `daily_plan_edit` (standard form view).

## 4. Questions/Assumptions
- We will assume "Items" are top-level `PlannedActivity` entries (parent=None).
- "Tasks" are children of Items.
- "Subtasks" are children of Tasks.
- We will use `start_time` and `end_time` relative to the `plan_date`.
