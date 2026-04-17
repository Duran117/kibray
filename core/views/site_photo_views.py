"""Site photo views — CRUD."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _generate_basic_pdf_from_html,
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
    _require_admin_or_redirect,
    _require_roles,
    _parse_date,
    _ensure_inventory_item,
    staff_required,
    logger,
    pisa,
    ROLES_ADMIN,
    ROLES_PM,
    ROLES_STAFF,
    ROLES_FIELD,
    ROLES_ALL_INTERNAL,
    ROLES_CLIENT_SIDE,
    ROLES_PROJECT_ACCESS,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


# ===========================
# ACTIVITY 1: DAILY PLAN ENHANCEMENTS
# ===========================

def site_photo_list(request, project_id):
    from core.models import Project, SitePhoto

    project = get_object_or_404(Project, pk=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url or "dashboard_client")
    
    photos = SitePhoto.objects.filter(project=project).order_by("-created_at")
    
    # Filter by photo type if specified
    photo_type = request.GET.get("type")
    if photo_type:
        photos = photos.filter(photo_type=photo_type)
    
    # Determine if user is a client
    profile = getattr(request.user, "profile", None)
    is_client_user = profile and profile.role == "client"
    
    return render(request, "core/site_photo_list.html", {
        "project": project, 
        "photos": photos,
        "is_client_user": is_client_user,
    })



@login_required
def site_photo_create(request, project_id):
    from core.forms import SitePhotoForm
    from core.models import Project, FloorPlan

    project = get_object_or_404(Project, pk=project_id)
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("name")
    
    if request.method == "POST":
        form = SitePhotoForm(request.POST, request.FILES, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = project
            obj.created_by = request.user
            try:
                obj.annotations = json.loads(form.cleaned_data.get("annotations") or "{}")
            except Exception:
                obj.annotations = {}
            obj.save()
            messages.success(request, _("Photo and annotations saved."))
            return redirect("site_photo_list", project_id=project.id)
    else:
        form = SitePhotoForm(project=project)
    return render(request, "core/site_photo_form.html", {
        "project": project, 
        "form": form,
        "floor_plans": floor_plans,
    })



@login_required
def site_photo_detail(request, photo_id):
    """View a single site photo with all its details."""
    from core.models import SitePhoto

    photo = get_object_or_404(SitePhoto, pk=photo_id)
    project = photo.project
    
    # Get adjacent photos for navigation
    all_photos = list(SitePhoto.objects.filter(project=project).order_by("-created_at").values_list("id", flat=True))
    current_index = all_photos.index(photo.id) if photo.id in all_photos else 0
    prev_photo_id = all_photos[current_index + 1] if current_index + 1 < len(all_photos) else None
    next_photo_id = all_photos[current_index - 1] if current_index > 0 else None
    
    profile = getattr(request.user, "profile", None)
    is_client_user = profile and profile.role == "client"
    
    return render(request, "core/site_photo_detail.html", {
        "photo": photo,
        "project": project,
        "is_client_user": is_client_user,
        "prev_photo_id": prev_photo_id,
        "next_photo_id": next_photo_id,
        "current_index": current_index + 1,
        "total_photos": len(all_photos),
    })



@login_required
@staff_required
def site_photo_edit(request, photo_id):
    """Edit an existing site photo."""
    from core.forms import SitePhotoForm
    from core.models import SitePhoto, FloorPlan

    photo = get_object_or_404(SitePhoto, pk=photo_id)
    project = photo.project
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("name")
    
    if request.method == "POST":
        form = SitePhotoForm(request.POST, request.FILES, instance=photo, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.annotations = json.loads(form.cleaned_data.get("annotations") or "{}")
            except Exception:
                pass
            obj.save()
            messages.success(request, _("Photo updated successfully."))
            return redirect("site_photo_detail", photo_id=photo.id)
    else:
        form = SitePhotoForm(instance=photo, project=project)
    
    return render(request, "core/site_photo_form.html", {
        "project": project,
        "form": form,
        "floor_plans": floor_plans,
        "photo": photo,
        "is_edit": True,
    })



@login_required
@staff_required
def site_photo_delete(request, photo_id):
    """Delete a site photo."""
    from core.models import SitePhoto

    photo = get_object_or_404(SitePhoto, pk=photo_id)
    project = photo.project
    
    if request.method == "POST":
        photo.delete()
        messages.success(request, _("Photo deleted successfully."))
        return redirect("site_photo_list", project_id=project.id)
    
    return render(request, "core/site_photo_confirm_delete.html", {
        "photo": photo,
        "project": project,
    })

