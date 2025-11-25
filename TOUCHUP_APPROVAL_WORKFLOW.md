# Touch-up Approval Workflow Guide

## Overview
The new approval system ensures that all completed touch-ups are reviewed by a Project Manager or Admin before being marked as officially complete.

---

## Workflow Steps

### 1️⃣ Employee Completes Touch-up
**Who**: Assigned employee/contractor  
**Action**: 
- Navigate to touch-up on floor plan
- Click "Completar" button
- Upload completion photos (optional but recommended)
- Submit completion form

**System Action**:
- Status changes to `completed`
- Approval status automatically set to `pending_review`
- Notification sent to PM/Admin (if configured)

---

### 2️⃣ PM Reviews Touch-up
**Who**: Project Manager or Admin  
**Action**:
- View touch-up details in modal
- Review completion photos
- Check work quality against specifications

**UI Display**:
```
┌──────────────────────────────────────┐
│ Estado de Aprobación:                │
│                                      │
│ 🕐 Pendiente de Revisión             │
│                                      │
│ [✅ Aprobar]  [❌ Rechazar]          │
└──────────────────────────────────────┘
```

---

### 3️⃣ Approval Decision

#### Option A: Approve ✅
**PM Action**: Click "Aprobar" button

**System Updates**:
```python
approval_status = 'approved'
reviewed_by = current_user
reviewed_at = now()
status = 'completed'  # Remains completed
```

**UI Display**:
```
┌──────────────────────────────────────┐
│ Estado de Aprobación:                │
│                                      │
│ ✓ Aprobado                           │
│   por John Doe el 15/01/2025         │
└──────────────────────────────────────┘
```

**Result**: Touch-up is officially complete ✓

---

#### Option B: Reject ❌
**PM Action**: 
1. Click "Rechazar" button
2. Enter rejection reason in prompt
3. Submit

**System Updates**:
```python
approval_status = 'rejected'
rejection_reason = "Falta pintura en esquina superior"
reviewed_by = current_user
reviewed_at = now()
status = 'in_progress'  # REOPENED for correction
```

**UI Display**:
```
┌──────────────────────────────────────┐
│ Estado de Aprobación:                │
│                                      │
│ ✗ Rechazado                          │
│   por John Doe el 15/01/2025         │
│                                      │
│ Razón:                               │
│ Falta pintura en esquina superior    │
└──────────────────────────────────────┘
```

**Result**: 
- Task reopens automatically
- Employee notified of rejection reason
- Employee must fix issues and resubmit

---

### 4️⃣ Re-completion (if rejected)
**Who**: Same assigned employee  
**Action**:
- Fix issues mentioned in rejection reason
- Complete touch-up again (follows Step 1)
- Upload new completion photos

**System Action**:
- Previous rejection reason is preserved
- New approval request created
- PM can review again

---

## Permission Matrix

| Role | View Status | Complete Touch-up | Approve | Reject |
|------|-------------|-------------------|---------|---------|
| **Admin** | ✅ | ✅ | ✅ | ✅ |
| **Project Manager** | ✅ | ✅ | ✅ | ✅ |
| **Employee** | ✅ | ✅ | ❌ | ❌ |
| **Contractor** | ✅ | ✅* | ❌ | ❌ |
| **Client** | ✅ | ❌ | ❌ | ❌ |
| **Designer** | ✅ | ❌ | ❌ | ❌ |

\* Only if assigned to the touch-up

---

## Status Flow Diagram

```
┌──────────────┐
│   pending    │ ← Initial creation
└──────┬───────┘
       │
       ▼ (Employee assigned)
┌──────────────┐
│ in_progress  │ ← Employee working
└──────┬───────┘
       │
       ▼ (Employee submits completion)
┌──────────────┐
│  completed   │
│              │
│ approval:    │
│ pending_     │
│ review       │
└──────┬───────┘
       │
       ├─────────────────┬──────────────┐
       ▼                 ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  completed   │  │ in_progress  │  │  completed   │
│              │  │              │  │              │
│ approval:    │  │ approval:    │  │ approval:    │
│ approved ✓   │  │ rejected ✗   │  │ pending...   │
│              │  │              │  │              │
│ FINAL STATE  │  │ REOPENED     │  │ AWAITING     │
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
                         │ (Fix & resubmit)
                         │
                         └──────────────┘
```

---

## UI Elements Reference

### Approval Status Badge
**Pending Review**:
```html
<span class="badge bg-warning text-dark">
    <i class="bi bi-clock"></i> Pendiente de Revisión
</span>
```

**Approved**:
```html
<div class="alert alert-success">
    <i class="bi bi-check-circle"></i> Aprobado
    por John Doe el 15/01/2025
</div>
```

**Rejected**:
```html
<div class="alert alert-danger">
    <i class="bi bi-x-circle"></i> Rechazado
    por John Doe el 15/01/2025
    <hr>
    <strong>Razón:</strong> Falta pintura en esquina superior
</div>
```

### Action Buttons (PM/Admin only)
```html
<button class="btn btn-success btn-sm" onclick="approveTouchup(123)">
    <i class="bi bi-check-circle"></i> Aprobar
</button>

<button class="btn btn-danger btn-sm" onclick="rejectTouchup(123)">
    <i class="bi bi-x-circle"></i> Rechazar
</button>
```

---

## API Endpoints

### Approve Touch-up
```
POST /touchups/{touchup_id}/approve/
Authorization: Required (PM/Admin)

Response:
{
    "success": true,
    "message": "Touch-up aprobado"
}
```

### Reject Touch-up
```
POST /touchups/{touchup_id}/reject/
Content-Type: application/x-www-form-urlencoded
Authorization: Required (PM/Admin)

Body:
reason=Falta+pintura+en+esquina+superior

Response:
{
    "success": true,
    "message": "Touch-up rechazado y reabierto"
}
```

---

## Database Schema

### TouchUpPin Model (Updated)
```python
class TouchUpPin(models.Model):
    # ... existing fields ...
    
    # Workflow status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('in_progress', 'En Progreso'),
            ('completed', 'Completado'),
            ('archived', 'Archivado')
        ],
        default='pending'
    )
    
    # Approval system (NEW)
    APPROVAL_CHOICES = [
        ('pending_review', 'Pendiente de Revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ]
    
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default='pending_review'
    )
    
    rejection_reason = models.TextField(blank=True)
    
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_touchups'
    )
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
```

---

## Best Practices

### For Employees
✅ **DO**:
- Upload clear completion photos
- Complete all work before marking as complete
- Check specifications before submitting

❌ **DON'T**:
- Rush completion to meet deadlines
- Skip photo documentation
- Ignore rejection feedback

### For Project Managers
✅ **DO**:
- Review completion photos carefully
- Provide specific rejection reasons
- Approve promptly if work is satisfactory
- Use rejection to maintain quality standards

❌ **DON'T**:
- Approve without reviewing
- Reject without clear explanation
- Delay approval unnecessarily
- Reject for minor issues (communicate instead)

---

## Reporting & Analytics

### Approval Metrics (Future Enhancement)
- Average approval time
- Rejection rate by employee
- Most common rejection reasons
- Touch-ups pending review count
- Quality control trends

### Dashboard Widgets
Current implementation shows:
- Pending touch-ups count
- In Progress count
- Completed count (includes approved)

Future: Separate "Approved" vs "Pending Review" counts

---

## Troubleshooting

### Issue: "Aprobar" button not showing
**Cause**: User doesn't have PM/Admin role  
**Solution**: Contact admin to update user role

### Issue: Rejection reason not saved
**Cause**: Empty reason submitted  
**Solution**: Enter a meaningful reason in the prompt

### Issue: Touch-up not reopening after rejection
**Cause**: Backend error in touchup_reject view  
**Solution**: Check server logs, verify migration 0062 applied

### Issue: Approval status not updating in UI
**Cause**: JavaScript error or network issue  
**Solution**: 
1. Check browser console for errors
2. Verify CSRF token is present
3. Reload page and try again

---

## Migration History

### Migration 0062 - Touch-up Approval System
**Created**: January 2025  
**Applied**: ✅ Verified

**Changes**:
```python
migrations.AddField(
    model_name='touchuppin',
    name='approval_status',
    field=models.CharField(default='pending_review', max_length=20),
)
migrations.AddField(
    model_name='touchuppin',
    name='rejection_reason',
    field=models.TextField(blank=True),
)
migrations.AddField(
    model_name='touchuppin',
    name='reviewed_by',
    field=models.ForeignKey(..., to=settings.AUTH_USER_MODEL),
)
migrations.AddField(
    model_name='touchuppin',
    name='reviewed_at',
    field=models.DateTimeField(blank=True, null=True),
)
```

**Rollback** (if needed):
```bash
python manage.py migrate core 0061
```

---

## Testing Checklist

### Employee Flow
- [ ] Complete a touch-up
- [ ] Upload completion photos
- [ ] Verify status shows "Pendiente de Revisión"
- [ ] Confirm no approve/reject buttons visible

### PM Flow
- [ ] View completed touch-up
- [ ] See approve/reject buttons
- [ ] Approve touch-up successfully
- [ ] Verify "Aprobado" badge appears
- [ ] Check reviewed_by and reviewed_at populated

### Rejection Flow
- [ ] Reject touch-up with reason
- [ ] Verify reason displays in UI
- [ ] Confirm task reopened (status = in_progress)
- [ ] Employee can see rejection reason
- [ ] Re-complete and verify new approval request

### Permissions
- [ ] Client cannot approve
- [ ] Designer cannot approve
- [ ] Unassigned employee cannot complete
- [ ] PM can approve any touch-up in their project

---

## Support & Documentation

**Related Files**:
- `core/models.py` - TouchUpPin model definition
- `core/views.py` - touchup_approve(), touchup_reject()
- `core/templates/core/touchup_plan_detail.html` - UI implementation
- `kibray_backend/urls.py` - URL routing

**Further Reading**:
- PANEL_REORGANIZATION_COMPLETE.md - Full implementation summary
- PANEL_REORGANIZATION_AUDIT.md - Original feature analysis

**Questions?**  
Contact the development team or check the system documentation.
