# Gantt Chart Drag & Drop Implementation

## Overview

This document describes the implementation of the Gantt chart drag & drop functionality that persists changes to the server in real-time.

## Architecture

### Frontend (React + TypeScript)

**Components:**
- `GanttChart.tsx` - Main Gantt visualization component using Frappe Gantt
- `App.tsx` - Parent container managing state and API calls

**API Layer:**
- `api.ts` - API client with specialized methods for Gantt updates

### Backend (Django REST Framework)

**Models:**
- `ScheduleItem` - Task/activity with dates, progress, and dependencies
- `ScheduleCategory` - Task categorization

**API Endpoints:**
- `PATCH /api/v1/schedule/items/{id}/` - Update individual task
- Accepts partial updates (only changed fields)

**Serializer:**
- `ScheduleItemSerializer` - Handles field mapping and validation
- Supports partial updates without requiring all fields

## User Flows

### 1. Drag & Drop Task (Date Change)

```
User Action: Drags task bar horizontally
    ↓
Frappe Gantt: Calculates new start/end dates
    ↓
GanttChart.tsx: on_date_change callback triggered
    ↓
App.tsx: handleGanttTaskUpdate() called
    ↓
api.ts: scheduleApi.updateTaskDates(id, start, end)
    ↓
PATCH /api/v1/schedule/items/{id}/
    {
      "planned_start": "2024-01-15",
      "planned_end": "2024-01-20"
    }
    ↓
Django: ScheduleItemSerializer validates & saves
    ↓
Response: Updated task data
    ↓
App.tsx: Updates local state
    ↓
GanttChart.tsx: Re-renders with persisted data
```

### 2. Resize Task (Date Range Change)

Same flow as drag & drop - both start and end dates updated.

### 3. Progress Bar Update

```
User Action: Drags progress bar handle
    ↓
Frappe Gantt: Calculates new progress percentage
    ↓
GanttChart.tsx: on_progress_change callback triggered
    ↓
App.tsx: handleGanttTaskUpdate() called
    ↓
api.ts: scheduleApi.updateTaskProgress(id, progress)
    ↓
PATCH /api/v1/schedule/items/{id}/
    {
      "percent_complete": 75
    }
    ↓
Django: Updates and saves
    ↓
Response: Updated task data
    ↓
UI reflects new progress
```

## Error Handling

### Frontend

1. **Network Errors:**
   - Display error message to user
   - Reload all tasks from server to revert visual changes
   - Auto-clear error message after 3 seconds

2. **Validation Errors:**
   - Show error alert
   - Revert to last known good state

3. **Visual Feedback:**
   - "Guardando cambios..." indicator during save
   - Spinner animation
   - Blue badge in controls area

### Backend

1. **Partial Update Validation:**
   - Serializer configured with `required=False` for optional fields
   - Only validates provided fields
   - Preserves unchanged fields

2. **Authentication:**
   - All endpoints require authentication
   - Returns 401/403 for unauthorized access

3. **Not Found:**
   - Returns 404 for non-existent task IDs

## API Methods

### scheduleApi.updateTaskDates()

```typescript
updateTaskDates: async (taskId: string, start: string, end: string): Promise<ScheduleTask>
```

**Purpose:** Optimized method for date-only updates (drag & drop).

**Parameters:**
- `taskId` - Task ID to update
- `start` - New start date in 'YYYY-MM-DD' format
- `end` - New end date in 'YYYY-MM-DD' format

**Returns:** Updated task object

**HTTP Request:**
```
PATCH /api/v1/schedule/items/{id}/
Content-Type: application/json

{
  "planned_start": "2024-01-15",
  "planned_end": "2024-01-20"
}
```

### scheduleApi.updateTaskProgress()

```typescript
updateTaskProgress: async (taskId: string, progress: number): Promise<ScheduleTask>
```

**Purpose:** Optimized method for progress-only updates.

**Parameters:**
- `taskId` - Task ID to update
- `progress` - New progress value (0-100)

**Returns:** Updated task object

**HTTP Request:**
```
PATCH /api/v1/schedule/items/{id}/
Content-Type: application/json

{
  "percent_complete": 75
}
```

## Serializer Configuration

### ScheduleItemSerializer

```python
class ScheduleItemSerializer(serializers.ModelSerializer):
    # Map frontend 'name' to model 'title'
    name = serializers.CharField(source="title", required=False)
    
    # Allow omitting category
    category = serializers.PrimaryKeyRelatedField(
        queryset=ScheduleCategory.objects.all(), 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = ScheduleItem
        fields = [...]
        # Enable partial updates
        extra_kwargs = {
            'project': {'required': False},
            'planned_start': {'required': False},
            'planned_end': {'required': False},
        }
```

**Key Features:**
- All fields marked as `required=False` for PATCH
- Field name mapping (`name` → `title`)
- Supports partial updates without validation errors

## ViewSet Configuration

### ScheduleItemViewSet

```python
class ScheduleItemViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter by project if provided
        project_id = self.request.query_params.get("project")
        qs = ScheduleItem.objects.select_related("project", "category", "cost_code")
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs.order_by("order")
```

**Key Features:**
- Authentication required
- Project filtering support
- Optimized queries with select_related

## Testing

### Test Coverage

8 comprehensive tests covering:

1. ✅ Date-only updates (drag & drop)
2. ✅ Progress-only updates (progress bar)
3. ✅ Combined date + progress updates
4. ✅ Partial updates without all fields
5. ✅ Field preservation (unchanged fields)
6. ✅ Invalid date range handling
7. ✅ Authentication enforcement
8. ✅ 404 for non-existent items

### Running Tests

```bash
pytest tests/test_gantt_drag_drop.py -v
```

**Expected Output:**
```
8 passed in 10.07s
```

## Performance Optimizations

1. **Optimistic Updates:**
   - UI updates immediately before server response
   - Reverts on error

2. **Minimal Payloads:**
   - Only send changed fields
   - Separate methods for dates vs. progress

3. **Efficient Queries:**
   - `select_related()` for related objects
   - Project filtering at database level

4. **Debounced Saves:**
   - Frappe Gantt handles drag debouncing
   - Only fires callback on drag end

## UI/UX Features

1. **Visual Feedback:**
   - Saving indicator appears during API calls
   - Spinner + "Guardando cambios..." text
   - Auto-hides on completion

2. **Error Recovery:**
   - Clear error messages
   - Automatic revert on failure
   - Retry mechanism via data reload

3. **View Modes:**
   - Day / Week / Month views
   - Persisted in localStorage

## Future Enhancements

1. **Dependency Updates:**
   - Automatically adjust dependent tasks
   - Cascade date changes

2. **Bulk Updates:**
   - Update multiple tasks in one request
   - Use existing `bulk_update` endpoint

3. **Conflict Detection:**
   - Optimistic locking with version field
   - Warn on concurrent edits

4. **Undo/Redo:**
   - Track change history
   - Allow reverting recent changes

5. **Real-time Sync:**
   - WebSocket updates for multi-user collaboration
   - Show other users' active edits

## Troubleshooting

### Issue: Changes not persisting

**Possible causes:**
1. Authentication failure (401/403)
2. Network error
3. Validation error (400)

**Solution:**
- Check browser console for errors
- Verify user is logged in
- Check Django logs for validation details

### Issue: UI reverts after drag

**Possible causes:**
1. API endpoint unreachable
2. CSRF token missing
3. Server error (500)

**Solution:**
- Check network tab in browser DevTools
- Verify CSRF token in request headers
- Check Django server logs

### Issue: Validation errors on partial update

**Possible causes:**
1. Serializer requires all fields
2. Field name mismatch

**Solution:**
- Verify serializer `extra_kwargs` configuration
- Check field name mapping (`name` → `title`)

## Related Documentation

- [Frappe Gantt Documentation](https://frappe.io/gantt)
- [Django REST Framework - Serializers](https://www.django-rest-framework.org/api-guide/serializers/)
- [React TypeScript Best Practices](https://react-typescript-cheatsheet.netlify.app/)

## Code Locations

**Frontend:**
- `frontend/src/components/GanttChart.tsx` - Main component
- `frontend/src/components/GanttChart.css` - Styles
- `frontend/src/App.tsx` - State management
- `frontend/src/api.ts` - API client

**Backend:**
- `core/api/views.py` - ScheduleItemViewSet
- `core/api/serializers.py` - ScheduleItemSerializer
- `core/models.py` - ScheduleItem model

**Tests:**
- `tests/test_gantt_drag_drop.py` - API integration tests

## Summary

The Gantt drag & drop implementation provides a seamless user experience with:
- ✅ Real-time persistence to Django backend
- ✅ Optimistic UI updates
- ✅ Comprehensive error handling
- ✅ Optimized API calls
- ✅ Full test coverage
- ✅ Visual feedback for all operations

Users can confidently drag tasks, resize bars, and adjust progress knowing changes are automatically saved to the server.
