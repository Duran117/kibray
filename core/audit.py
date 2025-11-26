"""
Audit logging utilities for automatic tracking of model changes
Phase 9: Security & Audit Trail
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from core.models import (
    AuditLog, LoginAttempt, Project, Task, Invoice, 
    Expense, InventoryMovement, DamageReport
)

User = get_user_model()


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit_action(user, action, entity_type, entity_id, entity_repr='', 
                     old_values=None, new_values=None, request=None, 
                     notes='', success=True, error_message=''):
    """
    Helper function to create audit log entries
    Can be called manually or via signals
    """
    username = user.username if user else 'system'
    
    audit_data = {
        'user': user if user else None,
        'username': username,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'entity_repr': entity_repr,
        'old_values': old_values,
        'new_values': new_values,
        'notes': notes,
        'success': success,
        'error_message': error_message,
    }
    
    if request:
        audit_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_id': request.session.session_key if hasattr(request, 'session') else '',
            'request_path': request.path,
            'request_method': request.method,
        })
    
    return AuditLog.objects.create(**audit_data)


# =============================================================================
# LOGIN/LOGOUT TRACKING
# =============================================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Track successful logins"""
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    session_id = request.session.session_key if hasattr(request, 'session') else ''
    
    # Log login attempt
    LoginAttempt.log_attempt(
        username=user.username,
        ip_address=ip,
        success=True,
        user_agent=user_agent,
        session_id=session_id
    )
    
    # Log audit trail
    log_audit_action(
        user=user,
        action='login',
        entity_type='user',
        entity_id=user.id,
        entity_repr=user.get_full_name() or user.username,
        request=request,
        notes='Successful login'
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Track logouts"""
    if user:
        log_audit_action(
            user=user,
            action='logout',
            entity_type='user',
            entity_id=user.id,
            entity_repr=user.get_full_name() or user.username,
            request=request,
            notes='User logged out'
        )


@receiver(user_login_failed)
def log_login_failure(sender, credentials, request, **kwargs):
    """Track failed login attempts"""
    username = credentials.get('username', 'unknown')
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Check if user exists to determine failure reason
    try:
        User.objects.get(username=username)
        failure_reason = 'invalid_password'
    except User.DoesNotExist:
        failure_reason = 'user_not_found'
    
    # Check rate limiting
    is_blocked, attempt_count = LoginAttempt.check_rate_limit(username, ip)
    if is_blocked:
        failure_reason = 'rate_limited'
    
    LoginAttempt.log_attempt(
        username=username,
        ip_address=ip,
        success=False,
        failure_reason=failure_reason,
        user_agent=user_agent
    )


# =============================================================================
# MODEL CHANGE TRACKING (Selective - only critical models)
# =============================================================================

# Store previous state before save
_pre_save_instances = {}

@receiver(pre_save, sender=Project)
@receiver(pre_save, sender=Invoice)
def capture_pre_save_state(sender, instance, **kwargs):
    """Capture state before save for comparison"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            _pre_save_instances[f"{sender.__name__}_{instance.pk}"] = original
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Project)
def audit_project_changes(sender, instance, created, **kwargs):
    """Track project creation and updates"""
    action = 'create' if created else 'update'
    
    old_values = None
    new_values = None
    
    if not created:
        key = f"{sender.__name__}_{instance.pk}"
        original = _pre_save_instances.get(key)
        if original:
            old_values = {
                'name': original.name,
                'status': original.status,
                'budget': str(original.budget),
                'client_id': original.client_id,
            }
            new_values = {
                'name': instance.name,
                'status': instance.status,
                'budget': str(instance.budget),
                'client_id': instance.client_id,
            }
            # Cleanup
            del _pre_save_instances[key]
    
    # Note: This will only track changes made through code, not from API with request context
    # For API tracking, see DRF middleware below
    log_audit_action(
        user=None,  # Will be enriched by API middleware
        action=action,
        entity_type='project',
        entity_id=instance.id,
        entity_repr=str(instance),
        old_values=old_values,
        new_values=new_values,
        notes=f'Project {action}d'
    )


@receiver(post_delete, sender=Project)
@receiver(post_delete, sender=Task)
@receiver(post_delete, sender=Invoice)
def audit_model_deletion(sender, instance, **kwargs):
    """Track deletion of critical models"""
    entity_type_map = {
        'Project': 'project',
        'Task': 'task',
        'Invoice': 'invoice',
    }
    
    entity_type = entity_type_map.get(sender.__name__, 'unknown')
    
    log_audit_action(
        user=None,  # Will be enriched by API middleware
        action='delete',
        entity_type=entity_type,
        entity_id=instance.id,
        entity_repr=str(instance),
        old_values={'deleted': True},
        notes=f'{sender.__name__} deleted'
    )


# =============================================================================
# DRF MIDDLEWARE FOR API REQUEST TRACKING
# =============================================================================

class AuditLogMiddleware:
    """
    Middleware to enrich audit logs with request context
    Should be added to MIDDLEWARE in settings.py
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request in thread-local for signal handlers
        if hasattr(request, 'user') and request.user.is_authenticated:
            # You can use thread-local storage here if needed
            pass
        
        response = self.get_response(request)
        
        # Log API access for sensitive endpoints
        if request.path.startswith('/api/v1/') and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if hasattr(request, 'user') and request.user.is_authenticated:
                # Extract entity info from path if possible
                # e.g., /api/v1/projects/5/ -> entity_type=project, entity_id=5
                path_parts = request.path.strip('/').split('/')
                if len(path_parts) >= 3:
                    entity_type = path_parts[2].rstrip('s')  # Remove trailing 's'
                    entity_id = path_parts[3] if len(path_parts) > 3 and path_parts[3].isdigit() else None
                    
                    action_map = {
                        'POST': 'create',
                        'PUT': 'update',
                        'PATCH': 'update',
                        'DELETE': 'delete',
                    }
                    
                    log_audit_action(
                        user=request.user,
                        action=action_map.get(request.method, 'update'),
                        entity_type=entity_type,
                        entity_id=int(entity_id) if entity_id else None,
                        entity_repr='',
                        request=request,
                        notes=f'API {request.method} request',
                        success=(200 <= response.status_code < 400)
                    )
        
        return response
