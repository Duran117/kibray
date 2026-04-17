"""Miscellaneous views — client requests, analytics, PDF downloads, etc."""
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


# --- CLIENT REQUESTS ---




# --- CLIENT REQUESTS ---
@login_required
def client_request_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        if not title:
            messages.error(request, _("Título es requerido"))
        else:
            from core.models import ClientRequest

            ClientRequest.objects.create(
                project=project, title=title, description=description, created_by=request.user
            )
            messages.success(request, _("Solicitud creada"))
            return redirect("client_requests_list", project_id=project.id)
    return render(request, "core/client_request_form.html", {"project": project})



@login_required
def client_requests_list(request, project_id=None):
    from core.models import ClientRequest

    if project_id:
        project = get_object_or_404(Project, id=project_id)
        
        # SECURITY: Check project access
        has_access, redirect_url = _check_user_project_access(request.user, project)
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect(redirect_url)
        
        qs = ClientRequest.objects.filter(project=project).order_by("-created_at")
        
        # For non-staff clients, only show their own requests
        if not request.user.is_staff:
            qs = qs.filter(created_by=request.user)
    else:
        # Without project_id
        if request.user.is_staff:
            # Staff can see all requests
            project = None
            qs = ClientRequest.objects.all().select_related("project").order_by("-created_at")
        else:
            # Clients see only their own requests across all their projects
            project = None
            client_project_ids = list(
                request.user.project_accesses.filter(is_active=True).values_list('project_id', flat=True)
            )
            qs = ClientRequest.objects.filter(
                created_by=request.user,
                project_id__in=client_project_ids
            ).select_related("project").order_by("-created_at")
    
    return render(request, "core/client_requests_list.html", {"project": project, "requests": qs})



@login_required
def client_request_convert_to_co(request, request_id):
    from core.models import ClientRequest

    cr = get_object_or_404(ClientRequest, id=request_id)
    if cr.change_order:
        messages.info(
            request,
            _("Esta solicitud ya fue convertida al CO #%(co_id)s.") % {"co_id": cr.change_order.id},
        )
        return redirect("client_requests_list", project_id=cr.project.id)
    if request.method == "POST":
        description = request.POST.get("description") or cr.description or cr.title
        amount_str = request.POST.get("amount") or "0"
        try:
            amt = Decimal(amount_str)
        except Exception:
            amt = Decimal("0")
        co = ChangeOrder.objects.create(
            project=cr.project, description=description, amount=amt, status="pending"
        )
        cr.change_order = co
        cr.status = "converted"
        cr.save()
        messages.success(request, _("Solicitud convertida al CO #%(co_id)s.") % {"co_id": co.id})
        return redirect("changeorder_detail", changeorder_id=co.id)
    return render(request, "core/client_request_convert.html", {"req": cr})


PRESET_PRODUCTS = [
    # Pinturas
    {
        "category": "paint",
        "category_label": "Pintura",
        "brand": "sherwin_williams",
        "brand_label": "Sherwin‑Williams",
        "product_name": "Emerald Interior",
        "unit": "gal",
    },
    {
        "category": "primer",
        "category_label": "Primer",
        "brand": "sherwin_williams",
        "brand_label": "Sherwin‑Williams",
        "product_name": "Multi‑Purpose Primer",
        "unit": "gal",
    },
    {
        "category": "paint",
        "category_label": "Pintura",
        "brand": "benjamin_moore",
        "brand_label": "Benjamin Moore",
        "product_name": "Regal Select",
        "unit": "gal",
    },
    # Stain / Laca
    {
        "category": "stain",
        "category_label": "Stain",
        "brand": "milesi",
        "brand_label": "Milesi",
        "product_name": "Interior Wood Stain",
        "unit": "liter",
    },
    {
        "category": "lacquer",
        "category_label": "Laca/Clear",
        "brand": "chemcraft",
        "brand_label": "Chemcraft",
        "product_name": "Clear Lacquer",
        "unit": "liter",
    },
    # Enmascarado / protección
    {
        "category": "tape",
        "category_label": "Tape",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "2090 ScotchBlue",
        "unit": "roll",
    },
    {
        "category": "plastic",
        "category_label": "Plástico",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Hand‑Masker Film 9ft",
        "unit": "roll",
    },
    {
        "category": "masking_paper",
        "category_label": "Papel enmascarar",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Hand‑Masker Brown Paper 12in",
        "unit": "roll",
    },
    {
        "category": "floor_paper",
        "category_label": "Papel para piso",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Ram Board",
        "unit": "roll",
    },
    # Herramientas
    {
        "category": "brush",
        "category_label": "Brocha",
        "brand": "purdy",
        "brand_label": "Purdy",
        "product_name": 'Pro‑Extra 2.5"',
        "unit": "unit",
    },
    {
        "category": "roller_cover",
        "category_label": "Rodillo (cover)",
        "brand": "wooster",
        "brand_label": "Wooster",
        "product_name": '9in Micro Plush 3/8"',
        "unit": "unit",
    },
    {
        "category": "tray_liner",
        "category_label": "Liner",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Liner para charola 9in",
        "unit": "pack",
    },
    {
        "category": "sandpaper",
        "category_label": "Lija",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "P220 Hookit",
        "unit": "box",
    },
    {
        "category": "blades",
        "category_label": "Cuchillas",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Cuchillas trapezoidales",
        "unit": "box",
    },
    # Selladores/PPE
    {
        "category": "caulk",
        "category_label": "Caulk/Sellador",
        "brand": "wurth",
        "brand_label": "Würth",
        "product_name": "Acrylic Latex Caulk (White)",
        "unit": "tube",
    },
    {
        "category": "respirator",
        "category_label": "Respirador",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Half Facepiece 6200",
        "unit": "unit",
    },
    {
        "category": "mask",
        "category_label": "Mascarilla",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "N95",
        "unit": "box",
    },
    {
        "category": "coverall",
        "category_label": "Overol",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Coverall desechable",
        "unit": "unit",
    },
    {
        "category": "gloves",
        "category_label": "Guantes",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Nitrilo",
        "unit": "box",
    },
]



@login_required
def photo_editor_standalone_view(request):
    """Standalone photo editor that opens in new tab/window"""
    return render(request, "core/photo_editor_standalone.html")



@login_required
def get_approved_colors(request, project_id):
    """API endpoint to get approved colors for a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    colors = (
        ColorSample.objects.filter(project_id=project_id, status="approved")
        .values("id", "code", "name", "brand", "finish")
        .order_by("code")
    )

    return JsonResponse({"colors": list(colors)})


    # (Legacy annotation and delete endpoints removed; use DRF versions under /api/v1/changeorder-photo/)


def color_sample_client_signature_view(request, sample_id, token=None):
    """Public view to capture client signature on color samples.
    Requires either a valid signed token OR an authenticated user.
    """
    color_sample = get_object_or_404(ColorSample, id=sample_id)

    # --- Access control: token OR authenticated user ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 days
            if payload.get("sample_id") != color_sample.id:
                return HttpResponseForbidden("Token does not match this color sample.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("The signature link has expired. Please request a new one.")
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid or tampered token.")
    elif not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # If already signed, show corresponding screen
    if color_sample.client_signature:
        return render(
            request,
            "core/color_sample_signature_already_signed.html",
            {"color_sample": color_sample},
        )

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signed_name = request.POST.get("signed_name", "").strip()

        if not signature_data:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {
                    "color_sample": color_sample,
                    "error": "Please draw your signature before continuing.",
                },
            )
        if not signed_name:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": "Please enter your full name."},
            )

        try:
            # --- Process base64 signature ---
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            if ext not in ["png", "jpeg", "jpg"]:
                ext = "png"

            # Decode base64
            decoded_image = base64.b64decode(imgstr)

            # Create unique filename
            file_name = f"color_sample_{color_sample.id}_signature_{uuid.uuid4().hex}.{ext}"
            signature_file = ContentFile(decoded_image, name=file_name)

            # Get client IP
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            client_ip = (
                x_forwarded_for.split(",")[0]
                if x_forwarded_for
                else request.META.get("REMOTE_ADDR", "")
            )

            # --- Save signature using the new model fields ---
            color_sample.sign_by_client(signature_file, signed_name, client_ip)

            # --- Queue background task for email/PDF (non-blocking) ---
            customer_email = request.POST.get("customer_email", "").strip()
            try:
                from core.tasks import process_signature_post_tasks
                process_signature_post_tasks.delay(
                    document_type="color_sample",
                    document_id=color_sample.id,
                    signer_name=signed_name,
                    customer_email=customer_email if customer_email else None,
                )
            except Exception:
                pass  # Don't block if task queueing fails

            # --- Generate download token for client ---
            from django.core import signing
            download_token = signing.dumps({"sample_id": color_sample.id})

            return render(
                request,
                "core/color_sample_signature_success.html",
                {"color_sample": color_sample, "download_token": download_token},
            )
        except Exception as e:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": f"Error processing the signature: {e}"},
            )

    return render(request, "core/color_sample_signature_form.html", {"color_sample": color_sample})



@login_required
def root_redirect(request):
    """Redirige al dashboard apropiado según rol del usuario"""
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)

    # Admin/Superuser → dashboard completo
    if request.user.is_superuser or request.user.is_staff:
        return redirect("dashboard_admin")

    # Según rol definido en Profile
    if role == "project_manager":
        return redirect("dashboard_pm")
    elif role == "client":
        return redirect("dashboard_client")
    elif role == "employee":
        return redirect("dashboard_employee")

    # Fallback
    return redirect("dashboard")



@login_required
def navigation_app_view(request):
    """
    Serves the React navigation SPA for Phase 4 features.
    This view handles client-side routing for paths like /files, /users, /calendar, etc.
    """
    return render(request, "navigation/index.html")



def set_language_view(request, code: str = ""):
    """Set language using Django's standard session/cookie key and persist on profile."""
    lang_code = (code or request.POST.get("language") or "").lower()
    supported = {c[0] for c in settings.LANGUAGES}
    if lang_code not in supported:
        lang_code = settings.LANGUAGE_CODE

    translation.activate(lang_code)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang_code

    # persist on user profile if logged in
    try:
        if request.user.is_authenticated:
            prof = getattr(request.user, "profile", None)
            if prof and prof.language != lang_code:
                prof.language = lang_code
                prof.save(update_fields=["language"])
    except Exception:
        pass

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("dashboard")
    response = redirect(next_url)

    # mirror Django's set_language cookie behavior
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", None),
        path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
        domain=getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None),
        secure=getattr(settings, "LANGUAGE_COOKIE_SECURE", False),
        httponly=getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False),
        samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", None),
    )
    return response



# --- DEMO: JavaScript i18n ---
@login_required
def js_i18n_demo(request):
    """
    Demo page showing how to use Django's JavaScript translation catalog.
    This demonstrates gettext(), ngettext(), and interpolate() in JavaScript.
    """
    return render(request, "core/js_i18n_demo.html")



# --- ANALYTICS DASHBOARD ---
@login_required
def analytics_dashboard(request):
    """
    Analytics Dashboard - Comprehensive metrics and KPIs.
    Shows: Project performance, employee stats, financial overview.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'admin')):
        messages.error(request, _("No tienes permiso para acceder a Analytics."))
        return redirect("dashboard")
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # === PROJECT METRICS ===
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(is_archived=False).count()
    archived_projects = Project.objects.filter(is_archived=True).count()
    
    # Projects this month
    projects_this_month = Project.objects.filter(created_at__gte=month_start).count()
    
    # === EMPLOYEE METRICS ===
    total_employees = Employee.objects.filter(is_active=True).count()
    
    # Hours this month
    month_hours = TimeEntry.objects.filter(
        date__gte=month_start,
        date__lte=today
    ).aggregate(total=Coalesce(Sum('hours_worked'), Decimal('0.00')))['total']
    
    # === CHANGE ORDER METRICS ===
    total_cos = ChangeOrder.objects.count()
    pending_cos = ChangeOrder.objects.filter(status='pending').count()
    approved_cos = ChangeOrder.objects.filter(status='approved').count()
    
    # CO value this month
    co_value_month = ChangeOrder.objects.filter(
        date_created__gte=month_start,
        status='approved'
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    # === TASKS METRICS ===
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='Completed').count()
    overdue_tasks = Task.objects.filter(
        due_date__lt=today
    ).exclude(status='Completed').exclude(status='Cancelled').count()
    
    task_completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
    
    # === TOP PROJECTS BY ACTIVITY ===
    top_projects = Project.objects.filter(
        is_archived=False
    ).annotate(
        task_count=Count('tasks'),
        co_count=Count('change_orders'),
        hours=Coalesce(Sum('timeentry__hours_worked'), Decimal('0.00'))
    ).order_by('-hours')[:5]
    
    # === TOP EMPLOYEES BY HOURS ===
    top_employees = Employee.objects.filter(
        is_active=True
    ).annotate(
        month_hours=Coalesce(
            Sum('timeentry__hours_worked', filter=Q(
                timeentry__date__gte=month_start,
                timeentry__date__lte=today
            )),
            Decimal('0.00')
        )
    ).filter(month_hours__gt=0).order_by('-month_hours')[:5]
    
    context = {
        # Project metrics
        'total_projects': total_projects,
        'active_projects': active_projects,
        'archived_projects': archived_projects,
        'projects_this_month': projects_this_month,
        # Employee metrics
        'total_employees': total_employees,
        'month_hours': month_hours,
        # Change order metrics
        'total_cos': total_cos,
        'pending_cos': pending_cos,
        'approved_cos': approved_cos,
        'co_value_month': co_value_month,
        # Task metrics
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'task_completion_rate': task_completion_rate,
        # Top lists
        'top_projects': top_projects,
        'top_employees': top_employees,
        # Date context
        'month_start': month_start,
        'today': today,
    }
    
    return render(request, "core/analytics_dashboard.html", context)



# --- COLOR APPROVALS REACT ---
@login_required
def color_approvals_react(request, project_id=None):
    """
    Color Approvals React view - serves React-based color approval management.
    """
    project = None
    if project_id:
        project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "core/color_approvals_react.html",
        {
            "project_id": project_id,
            "project": project,
        },
    )



# --- PM ASSIGNMENTS REACT ---
@login_required
def pm_assignments_react(request):
    """
    PM Assignments React view - serves React-based PM assignment management.
    """
    return render(request, "core/pm_assignments_react.html", {})



@login_required
def colorsample_pdf_download(request, colorsample_id):
    """
    Generate and download a professional PDF for a signed Color Sample.
    """
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    colorsample = get_object_or_404(ColorSample, pk=colorsample_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ColorSample_{colorsample.sample_number or colorsample.id}_{colorsample.code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('colorsample_list')



@login_required
def colorsample_pdf_view(request, colorsample_id):
    """
    View the Color Sample PDF inline in browser.
    """
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    colorsample = get_object_or_404(ColorSample, pk=colorsample_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ColorSample_{colorsample.id}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('colorsample_list')



@login_required
def estimate_pdf_download(request, estimate_id):
    """
    Generate and download a professional PDF for an Estimate.
    Query param: ?contract=1 to generate as contract format.
    """
    from core.services.pdf_service import generate_estimate_pdf
    
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    as_contract = request.GET.get('contract', '0') == '1'
    
    try:
        pdf_bytes = generate_estimate_pdf(estimate, as_contract=as_contract)
        
        doc_type = "Contract" if as_contract else "Estimate"
        filename = f"{doc_type}_{estimate.code}_{estimate.project.project_code}.pdf"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('estimate_list')



@login_required
def estimate_pdf_view(request, estimate_id):
    """
    View the Estimate/Contract PDF inline in browser.
    Query param: ?contract=1 to generate as contract format.
    """
    from core.services.pdf_service import generate_estimate_pdf
    
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    as_contract = request.GET.get('contract', '0') == '1'
    
    try:
        pdf_bytes = generate_estimate_pdf(estimate, as_contract=as_contract)
        
        doc_type = "Contract" if as_contract else "Estimate"
        filename = f"{doc_type}_{estimate.code}.pdf"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('estimate_list')



# =============================================================================
# EMPLOYEE SELF-SERVICE: Mi Nómina (My Payroll)
# =============================================================================

@login_required
def my_payroll(request):
    """
    Employee self-service page to view their own payroll information:
    - Recent payments (what they've received)
    - Savings balance (money held by company)
    - Work hours this week/month
    
    Accessible by ANY logged-in employee (who is linked to an Employee record).
    """
    from core.models import (
        Employee, PayrollPayment, PayrollRecord, EmployeeSavings, TimeEntry
    )
    from datetime import timedelta
    from decimal import Decimal
    
    # Get the employee record linked to this user
    employee = Employee.objects.filter(user=request.user).first()
    
    if not employee:
        messages.error(
            request, 
            _("Your user account is not linked to an employee record. Please contact your administrator.")
        )
        return redirect("dashboard")
    
    today = timezone.localdate()
    
    # === SAVINGS BALANCE ===
    savings_balance = EmployeeSavings.get_employee_balance(employee)
    savings_ledger = EmployeeSavings.get_employee_ledger(employee)[:20]  # Last 20 transactions
    
    # === RECENT PAYMENTS ===
    # Get PayrollRecords for this employee
    recent_payments = PayrollPayment.objects.filter(
        payroll_record__employee=employee
    ).select_related(
        'payroll_record', 'payroll_record__period'
    ).order_by('-payment_date')[:20]
    
    # Calculate payment stats
    # This month's payments
    month_start = today.replace(day=1)
    month_payments = PayrollPayment.objects.filter(
        payroll_record__employee=employee,
        payment_date__gte=month_start,
    )
    month_total_taken = sum(p.amount_taken for p in month_payments)
    month_total_saved = sum(p.amount_saved for p in month_payments)
    
    # === WORK HOURS ===
    # This week
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=week_start,
        date__lte=today,
    ).order_by('date', 'start_time')
    week_hours = sum(entry.hours_worked or 0 for entry in week_entries)
    
    # This month
    month_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=month_start,
        date__lte=today,
    )
    month_hours = sum(entry.hours_worked or 0 for entry in month_entries)
    
    # === YEAR-TO-DATE ===
    year_start = today.replace(month=1, day=1)
    ytd_payments = PayrollPayment.objects.filter(
        payroll_record__employee=employee,
        payment_date__gte=year_start,
    )
    ytd_total_received = sum(p.amount_taken for p in ytd_payments)
    ytd_total_saved = sum(p.amount_saved for p in ytd_payments)
    
    ytd_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=year_start,
    )
    ytd_hours = sum(entry.hours_worked or 0 for entry in ytd_entries)
    
    # Get employee's hourly rate (from PayrollRecord if available)
    hourly_rate = Decimal('0')
    latest_record = PayrollRecord.objects.filter(
        employee=employee,
        hourly_rate__gt=0
    ).order_by('-week_start').first()
    if latest_record:
        hourly_rate = latest_record.hourly_rate
    else:
        # Fallback to employee default
        hourly_rate = getattr(employee, 'hourly_rate', Decimal('0')) or Decimal('0')
    
    context = {
        "employee": employee,
        "hourly_rate": hourly_rate,
        # Savings
        "savings_balance": savings_balance,
        "savings_ledger": savings_ledger,
        # Payments
        "recent_payments": recent_payments,
        "month_total_taken": month_total_taken,
        "month_total_saved": month_total_saved,
        # Hours
        "week_entries": week_entries,
        "week_hours": week_hours,
        "month_hours": month_hours,
        # YTD
        "ytd_total_received": ytd_total_received,
        "ytd_total_saved": ytd_total_saved,
        "ytd_hours": ytd_hours,
        # Dates for context
        "today": today,
        "week_start": week_start,
        "month_start": month_start,
        "year_start": year_start,
    }
    
    return render(request, "core/my_payroll.html", context)



def colorsample_public_pdf_download(request, sample_id, token):
    """
    Public view to download Color Sample PDF after signing.
    Validates token (HMAC) with 30-day expiration.
    """
    from django.core import signing
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    colorsample = get_object_or_404(ColorSample, pk=sample_id)
    
    # Validate token
    try:
        payload = signing.loads(token, max_age=60 * 60 * 24 * 30)  # 30 days
        if payload.get("sample_id") != colorsample.id:
            return HttpResponseForbidden("Token does not match this Color Sample.")
    except signing.SignatureExpired:
        return HttpResponseForbidden("Download link has expired. Please contact us for a new link.")
    except signing.BadSignature:
        return HttpResponseForbidden("Invalid download link.")
    
    # Check if signed
    if not colorsample.client_signed_at:
        return HttpResponseForbidden("This Color Sample has not been approved yet.")
    
    try:
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ColorSample_{colorsample.sample_number or colorsample.id}_{colorsample.code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception(f"Error generating Color Sample PDF for sample #{colorsample.id}")
        return HttpResponse("Error generating PDF. Please try again later.", status=500)


# ========================================================================================
