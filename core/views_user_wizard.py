from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext as _
from django.template.loader import render_to_string
import json
import logging

from core.models import Profile, ROLE_CHOICES

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role in ['admin', 'owner'])

@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    """
    List users with filtering, search and pagination.
    """
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        
    if role_filter:
        users = users.filter(profile__role=role_filter)
        
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
            
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'query': query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': ROLE_CHOICES,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('core/wizards/partials/user_list_rows.html', context, request=request)
        return JsonResponse({'html': html, 'has_next': page_obj.has_next()})
        
    return render(request, 'core/wizards/user_list.html', context)

@login_required
@user_passes_test(is_admin)
def user_wizard_view(request, user_id=None):
    """
    Create or Edit user wizard.
    """
    user_obj = None
    if user_id:
        user_obj = get_object_or_404(User, pk=user_id)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'validate_step':
                return validate_user_step(data, user_obj)
            elif action == 'save':
                return save_user_wizard(data, user_obj, request.user)
                
        except Exception as e:
            logger.error(f"User Wizard Error: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
            
    context = {
        'target_user': user_obj,
        'roles': ROLE_CHOICES,
        'groups': Group.objects.all(),
        'is_edit': user_obj is not None
    }
    return render(request, 'core/wizards/user_wizard.html', context)

def validate_user_step(data, user_obj=None):
    """
    Validate specific step data.
    """
    step = data.get('step')
    errors = {}
    
    if step == 1: # Basic Info
        username = data.get('username')
        email = data.get('email')
        
        if not username:
            errors['username'] = _('Username is required.')
        elif User.objects.filter(username=username).exclude(pk=user_obj.pk if user_obj else None).exists():
            errors['username'] = _('Username already exists.')
            
        if not email:
            errors['email'] = _('Email is required.')
        elif User.objects.filter(email=email).exclude(pk=user_obj.pk if user_obj else None).exists():
            errors['email'] = _('Email already exists.')
            
    elif step == 2: # Password (only for creation or explicit change)
        password = data.get('password')
        confirm = data.get('confirm_password')
        if not user_obj and not password:
             errors['password'] = _('Password is required for new users.')
        
        if password:
            if password != confirm:
                errors['confirm_password'] = _('Passwords do not match.')
            if len(password) < 8:
                errors['password'] = _('Password must be at least 8 characters.')
                
    return JsonResponse({'success': not bool(errors), 'errors': errors})

def save_user_wizard(data, user_obj, admin_user):
    """
    Save user data from wizard.
    """
    try:
        # Basic Info
        username = data.get('username')
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        if not user_obj:
            user_obj = User(username=username)
        else:
            user_obj.username = username
            
        user_obj.email = email
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        
        # Password
        password = data.get('password')
        if password:
            user_obj.set_password(password)
            
        user_obj.save()
        
        # Profile / Role
        role = data.get('role', 'employee')
        if not hasattr(user_obj, 'profile'):
            Profile.objects.create(user=user_obj, role=role)
        else:
            user_obj.profile.role = role
            user_obj.profile.save()
            
        # Status
        is_active = data.get('is_active', True)
        user_obj.is_active = is_active
        user_obj.save()
        
        return JsonResponse({'success': True, 'user_id': user_obj.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
@require_POST
def user_api_action(request):
    """
    Handle actions like delete, toggle status, reset password.
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        user_id = data.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        
        if user.is_superuser and not request.user.is_superuser:
             return JsonResponse({'success': False, 'error': _('Permission denied.')})

        if action == 'toggle_status':
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({'success': True, 'new_status': user.is_active})
            
        elif action == 'delete':
            user.delete()
            return JsonResponse({'success': True})
            
        elif action == 'reset_password':
            # Generate a random password or handle logic
            # For now, we might just return success to trigger a UI modal for manual entry
            pass
            
        return JsonResponse({'success': False, 'error': 'Unknown action'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
