"""RFI, Issue, and Risk views — CRUD."""
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
@staff_member_required
def rfi_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RFIForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        number = (project.rfis.aggregate(m=models.Max("number"))["m"] or 0) + 1
        rfi = form.save(commit=False)
        rfi.project = project
        rfi.number = number
        rfi.save()
        return redirect("rfi_list", project_id=project.id)
    rfis = project.rfis.all()
    return render(request, "core/rfi_list.html", {"project": project, "rfis": rfis, "form": form})



@login_required
@staff_member_required
def rfi_answer_view(request, rfi_id):
    rfi = get_object_or_404(RFI, pk=rfi_id)
    form = RFIAnswerForm(request.POST or None, instance=rfi)
    if request.method == "POST" and form.is_valid():
        ans = form.save(commit=False)
        if ans.answer and ans.status == "open":
            ans.status = "answered"
        ans.save()
        return redirect("rfi_list", project_id=rfi.project_id)
    return render(request, "core/rfi_answer.html", {"rfi": rfi, "form": form})



@login_required
def rfi_edit_view(request, rfi_id):
    """Edit an RFI. Allowed for staff/PM."""
    rfi = get_object_or_404(RFI, pk=rfi_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("rfi_list", project_id=rfi.project_id)

    if request.method == "POST":
        form = RFIForm(request.POST, instance=rfi)
        if form.is_valid():
            form.save()
            messages.success(request, _("RFI actualizado."))
            return redirect("rfi_list", project_id=rfi.project_id)
    else:
        form = RFIForm(instance=rfi)
    return render(request, "core/rfi_form.html", {"form": form, "rfi": rfi, "project": rfi.project})



@login_required
def rfi_delete_view(request, rfi_id):
    """Delete an RFI with confirmation. Staff/PM only."""
    rfi = get_object_or_404(RFI, pk=rfi_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("rfi_list", project_id=rfi.project_id)

    project_id = rfi.project_id
    if request.method == "POST":
        rfi.delete()
        messages.success(request, _("RFI eliminado."))
        return redirect("rfi_list", project_id=project_id)
    return render(request, "core/rfi_confirm_delete.html", {"rfi": rfi})



@login_required
def issue_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = IssueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        isue = form.save(commit=False)
        isue.project = project
        isue.save()
        return redirect("issue_list", project_id=project.id)
    issues = project.issues.all()
    return render(
        request, "core/issue_list.html", {"project": project, "issues": issues, "form": form}
    )



@login_required
def issue_edit_view(request, issue_id):
    """Edit an Issue. Allowed for staff/PM."""
    issue = get_object_or_404(Issue, pk=issue_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("issue_list", project_id=issue.project_id)

    if request.method == "POST":
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, _("Issue actualizado."))
            return redirect("issue_list", project_id=issue.project_id)
    else:
        form = IssueForm(instance=issue)
    return render(
        request, "core/issue_form.html", {"form": form, "issue": issue, "project": issue.project}
    )



@login_required
def issue_delete_view(request, issue_id):
    """Delete an Issue with confirmation. Staff/PM only."""
    issue = get_object_or_404(Issue, pk=issue_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("issue_list", project_id=issue.project_id)

    project_id = issue.project_id
    if request.method == "POST":
        issue.delete()
        messages.success(request, _("Issue eliminado."))
        return redirect("issue_list", project_id=project_id)
    return render(request, "core/issue_confirm_delete.html", {"issue": issue})



@login_required
def risk_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RiskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rk = form.save(commit=False)
        rk.project = project
        rk.save()
        return redirect("risk_list", project_id=project.id)
    risks = project.risks.all()
    return render(
        request, "core/risk_list.html", {"project": project, "risks": risks, "form": form}
    )



@login_required
def risk_edit_view(request, risk_id):
    """Edit a Risk. Allowed for staff/PM."""
    risk = get_object_or_404(Risk, pk=risk_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("risk_list", project_id=risk.project_id)

    if request.method == "POST":
        form = RiskForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            messages.success(request, _("Risk actualizado."))
            return redirect("risk_list", project_id=risk.project_id)
    else:
        form = RiskForm(instance=risk)
    return render(
        request, "core/risk_form.html", {"form": form, "risk": risk, "project": risk.project}
    )



@login_required
def risk_delete_view(request, risk_id):
    """Delete a Risk with confirmation. Staff/PM only."""
    risk = get_object_or_404(Risk, pk=risk_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("risk_list", project_id=risk.project_id)

    project_id = risk.project_id
    if request.method == "POST":
        risk.delete()
        messages.success(request, _("Risk eliminado."))
        return redirect("risk_list", project_id=project_id)
    return render(request, "core/risk_confirm_delete.html", {"risk": risk})


