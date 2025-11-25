# Example: Integrating Push Notifications into Existing Views

## 1. Import the notification helpers

```python
# In your views.py or wherever you handle business logic
from core.notifications_push import (
    notify_changeorder_created,
    notify_changeorder_approved,
    notify_invoice_approved,
    notify_material_request,
    notify_task_assigned,
    notify_touchup_completed,
)
```

## 2. Add notification calls after creating/updating objects

### Example: Change Order Creation

```python
@login_required
def create_changeorder(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = ChangeOrderForm(request.POST, request.FILES)
        if form.is_valid():
            co = form.save(commit=False)
            co.project = project
            co.created_by = request.user
            co.save()
            
            # 🔔 Send push notification to admins
            notify_changeorder_created(co)
            
            messages.success(request, 'Change Order created successfully')
            return redirect('changeorder_board', project_id=project.id)
    else:
        form = ChangeOrderForm()
    
    return render(request, 'core/changeorder_form.html', {'form': form, 'project': project})
```

### Example: Change Order Approval

```python
@login_required
@require_POST
def approve_changeorder(request, co_id):
    co = get_object_or_404(ChangeOrder, id=co_id)
    
    # Check permissions
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    co.status = 'Approved'
    co.approved_by = request.user
    co.approved_at = timezone.now()
    co.save()
    
    # 🔔 Notify the requester
    notify_changeorder_approved(co)
    
    return JsonResponse({'success': True, 'status': 'Approved'})
```

### Example: Invoice Approval

```python
@login_required
def approve_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        invoice.status = 'Approved'
        invoice.approved_by = request.user
        invoice.approved_at = timezone.now()
        invoice.save()
        
        # 🔔 Notify PM
        notify_invoice_approved(invoice)
        
        messages.success(request, f'Invoice #{invoice.number} approved')
        return redirect('invoice_detail', invoice_id=invoice.id)
```

### Example: Material Request

```python
@login_required
def create_material_request(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = MaterialRequestForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.project = project
            material.requested_by = request.user
            material.save()
            
            # 🔔 Notify inventory managers
            notify_material_request(material)
            
            messages.success(request, 'Material request submitted')
            return redirect('dashboard_pm')
    else:
        form = MaterialRequestForm()
    
    return render(request, 'core/materials_request.html', {
        'form': form,
        'project': project
    })
```

### Example: Task Assignment

```python
@login_required
def assign_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        employee = get_object_or_404(User, id=employee_id)
        
        task.assigned_to = employee
        task.status = 'En Progreso'
        task.save()
        
        # 🔔 Notify assigned employee
        notify_task_assigned(task)
        
        messages.success(request, f'Task assigned to {employee.username}')
        return redirect('task_detail', task_id=task.id)
```

### Example: Touch-up Completion

```python
@login_required
def complete_touchup(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Verify user is assigned to this task
    if task.assigned_to != request.user:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    task.status = 'Completada'
    task.completed_at = timezone.now()
    task.save()
    
    # 🔔 Notify PM
    notify_touchup_completed(task)
    
    return JsonResponse({'success': True})
```

## 3. Signals-Based Approach (Recommended)

For cleaner code, use Django signals to trigger notifications automatically:

```python
# In core/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from core.models import ChangeOrder, Invoice, Task, MaterialRequest
from core.notifications_push import (
    notify_changeorder_created,
    notify_changeorder_approved,
    notify_invoice_approved,
    notify_material_request,
    notify_task_assigned,
)

@receiver(post_save, sender=ChangeOrder)
def on_changeorder_created(sender, instance, created, **kwargs):
    """Send notification when change order is created"""
    if created:
        notify_changeorder_created(instance)

@receiver(pre_save, sender=ChangeOrder)
def on_changeorder_approved(sender, instance, **kwargs):
    """Send notification when change order status changes to approved"""
    if instance.pk:
        old_instance = ChangeOrder.objects.get(pk=instance.pk)
        if old_instance.status != 'Approved' and instance.status == 'Approved':
            # Will be sent after save completes
            instance._notify_approved = True

@receiver(post_save, sender=ChangeOrder)
def send_changeorder_approval_notification(sender, instance, **kwargs):
    """Actually send the approval notification"""
    if hasattr(instance, '_notify_approved') and instance._notify_approved:
        notify_changeorder_approved(instance)
        delattr(instance, '_notify_approved')

@receiver(post_save, sender=Invoice)
def on_invoice_approved(sender, instance, **kwargs):
    """Send notification when invoice is approved"""
    if instance.status == 'Approved' and instance.approved_at:
        notify_invoice_approved(instance)

@receiver(post_save, sender=MaterialRequest)
def on_material_request_created(sender, instance, created, **kwargs):
    """Send notification when material is requested"""
    if created:
        notify_material_request(instance)

@receiver(post_save, sender=Task)
def on_task_assigned(sender, instance, created, **kwargs):
    """Send notification when task is assigned"""
    if not created and instance.assigned_to:
        # Check if assignment changed
        old_instance = Task.objects.get(pk=instance.pk)
        if old_instance.assigned_to != instance.assigned_to:
            notify_task_assigned(instance)
```

Then in `core/apps.py`:

```python
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals  # Import signals
```

## 4. Testing Notifications

### Test in Django Shell

```python
python manage.py shell

from core.models import ChangeOrder
from core.notifications_push import notify_changeorder_created

# Get a change order
co = ChangeOrder.objects.first()

# Send test notification
notify_changeorder_created(co)
```

### Test from OneSignal Dashboard

1. Go to OneSignal dashboard
2. Click "Messages" → "New Push"
3. Select your app
4. Compose test message
5. Click "Send to Test Users"
6. Verify notification appears in browser

## 5. User Preferences (Future Enhancement)

Create a user preferences model:

```python
class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Category preferences
    invoices_enabled = models.BooleanField(default=True)
    projects_enabled = models.BooleanField(default=True)
    tasks_enabled = models.BooleanField(default=True)
    materials_enabled = models.BooleanField(default=True)
    budget_enabled = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_end = models.TimeField(null=True, blank=True)    # e.g., 08:00
    
    # Sound preference
    sound_enabled = models.BooleanField(default=True)
    
    def is_quiet_time(self):
        """Check if current time is in quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        from django.utils import timezone
        now = timezone.localtime(timezone.now()).time()
        
        if self.quiet_start < self.quiet_end:
            return self.quiet_start <= now <= self.quiet_end
        else:
            # Overnight quiet hours
            return now >= self.quiet_start or now <= self.quiet_end
```

Then check preferences before sending:

```python
def notify_changeorder_created(change_order):
    """Notify admin when change order is created"""
    # ... existing code ...
    
    # Filter users by preferences
    users_to_notify = []
    for admin in admins:
        try:
            pref = admin.notificationpreference
            if pref.projects_enabled and not pref.is_quiet_time():
                users_to_notify.append(admin.pk)
        except NotificationPreference.DoesNotExist:
            # Default: send notification
            users_to_notify.append(admin.pk)
    
    if users_to_notify:
        PushNotificationService.send_notification(
            user_ids=users_to_notify,
            # ... rest of code
        )
```
