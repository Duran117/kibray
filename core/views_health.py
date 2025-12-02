"""
Health Check Views
Endpoints for monitoring application health and status
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
import os


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if application is running
    """
    return JsonResponse({
        "status": "healthy",
        "service": "kibray",
        "environment": os.getenv("DJANGO_ENV", "unknown"),
    })


@csrf_exempt
@require_http_methods(["GET"])
def health_check_detailed(request):
    """
    Detailed health check with dependency status
    Checks database, cache, and other services
    """
    health = {
        "status": "healthy",
        "service": "kibray",
        "environment": os.getenv("DJANGO_ENV", "unknown"),
        "checks": {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check cache (Redis)
    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            health["checks"]["cache"] = "healthy"
        else:
            health["checks"]["cache"] = "unhealthy: cache not working"
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["cache"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # Check static files
    from django.conf import settings
    if hasattr(settings, 'STATIC_ROOT'):
        if os.path.exists(settings.STATIC_ROOT):
            health["checks"]["static_files"] = "healthy"
        else:
            health["checks"]["static_files"] = "warning: static root not found"
            health["status"] = "degraded"
    
    # HTTP status code based on health
    status_code = 200 if health["status"] == "healthy" else 503
    
    return JsonResponse(health, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Kubernetes/Cloud readiness probe
    Checks if app is ready to receive traffic
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({"ready": True}, status=200)
    except Exception as e:
        return JsonResponse({"ready": False, "error": str(e)}, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Kubernetes/Cloud liveness probe
    Checks if app is alive (basic response)
    """
    return JsonResponse({"alive": True}, status=200)
