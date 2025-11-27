"""
Security decorators and utilities for Kibray construction management system.
Provides enhanced permission checks, CSRF protection, and rate limiting for sensitive operations.

Created during comprehensive security audit and optimization.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods


def require_role(*allowed_roles):
    """
    Decorator to restrict view access based on user role from Profile model.

    Usage:
        @require_role('admin', 'project_manager')
        def my_view(request):
            ...

    Allowed roles: admin, project_manager, client, employee, designer, superintendent
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            user_role = getattr(profile, "role", None)

            # Superusers always pass
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check role
            if user_role in allowed_roles or request.user.is_staff:
                return view_func(request, *args, **kwargs)

            # Denied
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": "Insufficient permissions"}, status=403)
            return HttpResponseForbidden("You don't have permission to access this resource.")

        return _wrapped_view

    return decorator


def ajax_login_required(view_func):
    """
    Decorator for AJAX views that returns JSON error instead of redirect on auth failure.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def ajax_csrf_protect(view_func):
    """
    CSRF protection for AJAX endpoints that returns JSON error instead of 403 page.
    """

    @wraps(view_func)
    @csrf_protect
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            if "CSRF" in str(e):
                return JsonResponse({"error": "CSRF verification failed"}, status=403)
            raise

    return _wrapped_view


def require_project_access(param_name="project_id"):
    """
    Decorator to verify user has access to specified project.
    Checks:
    - Staff/superuser: always allowed
    - Client role: must have ClientProjectAccess or match project.client
    - PM role: always allowed
    - Others: denied

    Usage:
        @require_project_access('project_id')
        def my_view(request, project_id):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            from core.models import ClientProjectAccess, Project

            # Get project_id from URL params
            project_id = kwargs.get(param_name)
            if not project_id:
                return HttpResponseBadRequest("Project ID required")

            # Get project
            project = get_object_or_404(Project, id=project_id)

            # Superuser/staff always allowed
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)

            # Check role-based access
            profile = getattr(request.user, "profile", None)
            role = getattr(profile, "role", None)

            # Project managers always allowed
            if role == "project_manager":
                return view_func(request, *args, **kwargs)

            # Clients need explicit access
            if role == "client":
                has_access = ClientProjectAccess.objects.filter(user=request.user, project=project).exists()
                legacy_access = project.client == request.user.username

                if has_access or legacy_access:
                    return view_func(request, *args, **kwargs)

            # Deny
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": "No access to this project"}, status=403)
            return HttpResponseForbidden("You don't have access to this project.")

        return _wrapped_view

    return decorator


def rate_limit(key_prefix="rl", max_requests=10, window_seconds=60):
    """
    Simple rate limiting decorator using Django cache.

    Usage:
        @rate_limit(key_prefix='invoice_submit', max_requests=5, window_seconds=300)
        def submit_invoice(request):
            ...

    Args:
        key_prefix: Unique identifier for this endpoint
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Build cache key using user ID or IP
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"

            cache_key = f"{key_prefix}_{identifier}"

            # Get current count
            current_requests = cache.get(cache_key, 0)

            if current_requests >= max_requests:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"error": f"Rate limit exceeded. Try again in {window_seconds} seconds."}, status=429
                    )
                return HttpResponseForbidden(
                    f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
                )

            # Increment counter
            cache.set(cache_key, current_requests + 1, window_seconds)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def sanitize_json_input(view_func):
    """
    Decorator to sanitize and validate JSON input from request.
    Prevents injection attacks through JSON fields.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        import html
        import json

        if request.method == "POST" and request.content_type == "application/json":
            try:
                data = json.loads(request.body)

                # Recursively sanitize strings in JSON
                def sanitize_value(value):
                    if isinstance(value, str):
                        # Escape HTML to prevent XSS
                        return html.escape(value)
                    elif isinstance(value, dict):
                        return {k: sanitize_value(v) for k, v in value.items()}
                    elif isinstance(value, list):
                        return [sanitize_value(item) for item in value]
                    return value

                request.sanitized_json = sanitize_value(data)

            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def require_post_with_csrf(view_func):
    """
    Combined decorator requiring POST method and CSRF protection.
    Use for all state-changing endpoints.
    """

    @wraps(view_func)
    @require_http_methods(["POST"])
    @csrf_protect
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# Utility function for checking staff-like permissions
def is_staffish(user):
    """
    Check if user has staff-level permissions (admin, PM, or Django staff).

    Args:
        user: Django User object

    Returns:
        bool: True if user has staff permissions
    """
    if user.is_superuser or user.is_staff:
        return True

    profile = getattr(user, "profile", None)
    if profile:
        role = getattr(profile, "role", None)
        return role in ("admin", "project_manager")

    return False
