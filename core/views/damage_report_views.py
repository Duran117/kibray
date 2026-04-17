"""Damage report views — CRUD, photos, status updates."""
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


@login_required
def damage_report_list(request, project_id):
    """Lista y creación de reportes de daños del proyecto."""
    from core.forms import DamageReportForm
    from core.models import DamagePhoto

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    # Handle creation
    if request.method == "POST":
        form = DamageReportForm(project, request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.project = project
            report.reported_by = request.user
            report.save()

            # Handle multiple photo uploads
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                DamagePhoto.objects.create(
                    report=report, image=photo_file, notes=request.POST.get("photo_notes", "")
                )

            messages.success(
                request, _("Reporte creado con %(count)s foto(s)") % {"count": len(photos)}
            )
            return redirect("damage_report_detail", report_id=report.id)
    else:
        form = DamageReportForm(project)

    # List reports
    reports = project.damage_reports.select_related("plan", "pin", "reported_by").all()
    severity = request.GET.get("severity")
    if severity:
        reports = reports.filter(severity=severity)
    status = request.GET.get("status")
    if status:
        reports = reports.filter(status=status)

    return render(
        request,
        "core/damage_report_list.html",
        {
            "project": project,
            "reports": reports,
            "form": form,
            "filter_severity": severity,
            "filter_status": status,
        },
    )



@login_required
def damage_report_detail(request, report_id):
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    return render(
        request,
        "core/damage_report_detail.html",
        {
            "report": report,
            "project": report.project,
        },
    )



@login_required
def damage_report_edit(request, report_id):
    """Edit an existing damage report."""
    from core.forms import DamageReportForm
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    project = report.project
    profile = getattr(request.user, "profile", None)
    can_edit = (
        request.user.is_staff
        or (profile and profile.role in ROLES_FIELD)
        or (request.user == report.reported_by)
    )
    if not can_edit:
        messages.error(request, "Acceso denegado.")
        return redirect("damage_report_detail", report_id=report.id)
    if request.method == "POST":
        form = DamageReportForm(project, request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Reporte actualizado.")
            return redirect("damage_report_detail", report_id=report.id)
    else:
        form = DamageReportForm(project, instance=report)
    return render(
        request,
        "core/damage_report_form.html",
        {
            "form": form,
            "project": project,
            "report": report,
            "is_edit": True,
        },
    )



@login_required
def damage_report_delete(request, report_id):
    """Delete a damage report with confirmation."""
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    project = report.project
    profile = getattr(request.user, "profile", None)
    can_delete = (
        request.user.is_staff
        or (profile and profile.role in ROLES_FIELD)
        or (request.user == report.reported_by)
    )
    if not can_delete:
        messages.error(request, "Acceso denegado.")
        return redirect("damage_report_detail", report_id=report.id)
    if request.method == "POST":
        project_id = project.id
        report.delete()
        messages.success(request, "Reporte de daño eliminado.")
        return redirect("damage_report_list", project_id=project_id)
    return render(
        request,
        "core/damage_report_confirm_delete.html",
        {
            "project": project,
            "report": report,
        },
    )



@login_required
def damage_report_add_photos(request, report_id):
    """Add multiple photos to existing damage report."""
    from core.models import DamagePhoto, DamageReport

    report = get_object_or_404(DamageReport, id=report_id)

    # Check permission
    if not (request.user.is_staff or request.user == report.reported_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        photos = request.FILES.getlist("photos")
        if not photos:
            return JsonResponse({"error": gettext("No se enviaron fotos")}, status=400)

        # Create DamagePhoto for each uploaded image
        created_count = 0
        for photo_file in photos:
            notes = request.POST.get("notes", "")
            DamagePhoto.objects.create(report=report, image=photo_file, notes=notes)
            created_count += 1

        return JsonResponse(
            {
                "success": True,
                "count": created_count,
                "message": f"{created_count} foto(s) agregada(s) correctamente",
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def damage_report_update_status(request, report_id):
    """Update damage report status and severity."""
    report = get_object_or_404(DamageReport, id=report_id)

    # Check permission (staff or superintendent)
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role == "superintendent")):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("status")
        new_severity = request.POST.get("severity")

        if new_status and new_status in dict(DamageReport.STATUS_CHOICES):
            report.status = new_status
            report.save()

        if new_severity and new_severity in dict(DamageReport.SEVERITY_CHOICES):
            report.severity = new_severity
            report.save()

        return JsonResponse(
            {
                "success": True,
                "status": report.get_status_display(),
                "severity": report.get_severity_display(),
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


