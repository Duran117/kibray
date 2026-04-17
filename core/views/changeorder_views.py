"""Change Order views — CRUD, signatures, board, PDF."""
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


# --- CHANGE ORDER ---
@login_required
def changeorder_detail_view(request, changeorder_id):
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Compute T&M preview if applicable
    tm_preview = None
    if changeorder.pricing_type == "T_AND_M":
        from core.services.financial_service import ChangeOrderService

        tm_preview = ChangeOrderService.get_billable_amount(changeorder)

    # Enrich time entries and expenses for real-time cost display
    time_entries = list(
        changeorder.time_entries.select_related("employee")
        .order_by("-date", "-start_time")
    )
    expenses = list(
        changeorder.expenses.all().order_by("-date")
    )
    is_admin = request.user.is_staff or request.user.is_superuser

    # Compute cost breakdown for both FIXED and T&M
    billing_rate = changeorder.get_effective_billing_rate()
    total_labor_hours = sum(
        (te.hours_worked or 0) for te in time_entries
    )
    total_labor_cost = float(total_labor_hours) * float(billing_rate)
    total_material_cost = sum(float(e.amount or 0) for e in expenses)
    markup_pct = float(changeorder.material_markup_percent or 0)
    total_material_with_markup = total_material_cost * (1 + markup_pct / 100)
    grand_total = total_labor_cost + total_material_with_markup

    cost_data = {
        "billing_rate": billing_rate,
        "total_labor_hours": total_labor_hours,
        "total_labor_cost": round(total_labor_cost, 2),
        "total_material_cost": round(total_material_cost, 2),
        "markup_pct": markup_pct,
        "total_material_with_markup": round(total_material_with_markup, 2),
        "grand_total": round(grand_total, 2),
        "labor_pct": round((total_labor_cost / grand_total * 100) if grand_total > 0 else 0, 1),
        "material_pct": round((total_material_with_markup / grand_total * 100) if grand_total > 0 else 0, 1),
        "time_entry_count": len(time_entries),
        "expense_count": len(expenses),
    }

    return render(
        request,
        "core/changeorder_detail_standalone.html",
        {
            "changeorder": changeorder,
            "tm_preview": tm_preview,
            "time_entries": time_entries,
            "expenses": expenses,
            "cost_data": cost_data,
            "is_admin": is_admin,
        },
    )



@login_required
def changeorder_billing_history_view(request, changeorder_id):
    """
    Billing history report for a Change Order.
    Shows all InvoiceLines with breakdown of labor vs materials.
    Admin/PM only.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Get all invoice lines related to this CO through TimeEntry or Expense
    from django.db.models import Q

    from core.models import InvoiceLine

    invoice_lines = (
        InvoiceLine.objects.filter(
            Q(time_entry__change_order=changeorder) | Q(expense__change_order=changeorder)
        )
        .select_related("invoice")
        .distinct()
        .order_by("-invoice__date_issued", "id")
    )

    # Separate labor and material lines
    labor_lines = []
    material_lines = []

    for line in invoice_lines:
        # Get related time entries and expenses
        time_entries = []
        expenses = []

        if line.time_entry and line.time_entry.change_order == changeorder:
            time_entries = [line.time_entry]

        if line.expense and line.expense.change_order == changeorder:
            expenses = [line.expense]

        line_data = {
            "invoice_line": line,
            "time_entries": time_entries,
            "expenses": expenses,
        }

        # Check if it's labor or materials based on description or related entries
        if (
            time_entries
            or "labor" in line.description.lower()
            or "mano de obra" in line.description.lower()
        ):
            labor_lines.append(line_data)
        else:
            material_lines.append(line_data)

    # Calculate totals
    total_labor = sum(line_item["invoice_line"].amount for line_item in labor_lines)
    total_materials = sum(line_item["invoice_line"].amount for line_item in material_lines)
    grand_total = total_labor + total_materials

    context = {
        "changeorder": changeorder,
        "labor_lines": labor_lines,
        "material_lines": material_lines,
        "total_labor": total_labor,
        "total_materials": total_materials,
        "grand_total": grand_total,
    }

    return render(request, "core/changeorder_billing_history.html", context)



@login_required
def changeorder_cost_breakdown_view(request, changeorder_id):
    """
    Vista estilo factura para mostrar el desglose de costos de un Change Order.
    Separa Materiales vs Mano de Obra para fácil envío al cliente.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    from decimal import Decimal

    from django.db.models import Sum

    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Get all expenses associated with this CO, separated by category
    material_expenses = changeorder.expenses.filter(
        category__in=["MATERIALES", "ALMACÉN"]
    ).order_by("date")
    other_expenses = changeorder.expenses.exclude(
        category__in=["MATERIALES", "ALMACÉN", "MANO_OBRA"]
    ).order_by("date")

    # Get all time entries for labor costs
    time_entries = changeorder.time_entries.select_related("employee").order_by("date")

    # Calculate totals
    total_materials = material_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_other_expenses = other_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Labor cost from TimeEntries
    labor_cost = sum(entry.labor_cost for entry in time_entries)
    total_hours = sum((entry.hours_worked or Decimal("0")) for entry in time_entries)

    # Apply markup if CO has T&M pricing
    material_markup_pct = Decimal("0")
    billing_rate = Decimal("50.00")  # Default rate

    if hasattr(changeorder, "pricing_type") and changeorder.pricing_type == "T_AND_M":
        material_markup_pct = changeorder.material_markup_percent or Decimal("0")
        billing_rate = changeorder.get_effective_billing_rate() if hasattr(changeorder, "get_effective_billing_rate") else Decimal("50.00")

    # Calculate billable amounts with markup
    material_with_markup = total_materials * (1 + material_markup_pct / Decimal("100"))
    labor_billable = total_hours * billing_rate

    # Grand totals
    subtotal_cost = total_materials + labor_cost + total_other_expenses
    subtotal_billable = material_with_markup + labor_billable + total_other_expenses
    profit_margin = subtotal_billable - subtotal_cost if subtotal_billable > 0 else Decimal("0.00")

    context = {
        "changeorder": changeorder,
        "material_expenses": material_expenses,
        "other_expenses": other_expenses,
        "time_entries": time_entries,
        "total_materials": total_materials,
        "total_other_expenses": total_other_expenses,
        "labor_cost": labor_cost,
        "total_hours": total_hours,
        "material_markup_pct": material_markup_pct,
        "billing_rate": billing_rate,
        "material_with_markup": material_with_markup,
        "labor_billable": labor_billable,
        "subtotal_cost": subtotal_cost,
        "subtotal_billable": subtotal_billable,
        "profit_margin": profit_margin,
    }

    return render(request, "core/changeorder_cost_breakdown.html", context)



def changeorder_customer_signature_view(request, changeorder_id, token=None):
    """Vista pública para capturar firma de cliente en Change Orders.
    Requires either a valid signed token OR an authenticated user with access.
    """
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # --- Calculate T&M total if applicable ---
    tm_breakdown = None
    if changeorder.pricing_type == 'T_AND_M':
        from core.services.financial_service import ChangeOrderService
        tm_breakdown = ChangeOrderService.get_billable_amount(changeorder)

    # --- Access control: token OR authenticated user ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 days
            if payload.get("co") != changeorder.id:
                return HttpResponseForbidden("Token does not match this Change Order.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("The signature link has expired. Please request a new one.")
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid or tampered token.")
    elif not request.user.is_authenticated:
        # No token and not logged in — block access
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # If already signed, show corresponding screen
    if changeorder.signature_image:
        return render(
            request, "core/changeorder_signature_already_signed.html", {
                "changeorder": changeorder,
                "tm_breakdown": tm_breakdown,
            }
        )

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signer_name = request.POST.get("signer_name", "").strip()

        if not signature_data:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": "Please draw your signature before continuing.",
                },
            )
        if not signer_name:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": "Please enter your full name.",
                },
            )

        try:
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            signature_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"signature_co_{changeorder.id}_{uuid.uuid4().hex[:8]}.{ext}",
            )

            changeorder.signature_image = signature_file
            changeorder.signed_by = signer_name
            changeorder.signed_at = timezone.now()
            changeorder.status = "approved"
            # Audit trail capture (Paso 4)
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            ip = (
                forwarded_for.split(",")[0].strip()
                if forwarded_for
                else request.META.get("REMOTE_ADDR")
            )
            changeorder.signed_ip = ip
            changeorder.signed_user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            changeorder.save(
                update_fields=[
                    "signature_image",
                    "signed_by",
                    "signed_at",
                    "status",
                    "signed_ip",
                    "signed_user_agent",
                ]
            )

            # --- Process heavy tasks in background (emails, PDF, storage) ---
            customer_email = request.POST.get("customer_email", "").strip()
            try:
                from core.tasks import process_signature_post_tasks
                process_signature_post_tasks.delay(
                    document_type="changeorder",
                    document_id=changeorder.id,
                    signer_name=signer_name,
                    customer_email=customer_email,
                )
            except Exception as task_error:
                # If Celery is not available, log but don't block
                logger.warning(f"Background task failed, will process inline: {task_error}")
                # Fallback: process synchronously but with timeout protection
                try:
                    from core.services.email_service import KibrayEmailService
                    from core.services.pdf_service import generate_signed_changeorder_pdf
                    
                    # Just generate PDF, skip emails if task queue is down
                    pdf_bytes = generate_signed_changeorder_pdf(changeorder)
                    if pdf_bytes:
                        changeorder.signed_pdf = ContentFile(
                            pdf_bytes, name=f"co_{changeorder.id}_signed.pdf"
                        )
                        changeorder.save(update_fields=["signed_pdf"])
                except Exception:
                    pass  # Don't block the signature success

            # --- Generate download token for client ---
            download_token = signing.dumps({"changeorder_id": changeorder.id})

            return render(
                request, "core/changeorder_signature_success.html", {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "download_token": download_token,
                }
            )
        except Exception as e:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": f"Error processing the signature: {e}",
                },
            )

    return render(request, "core/changeorder_signature_form.html", {
        "changeorder": changeorder,
        "tm_breakdown": tm_breakdown,
    })



@login_required
def changeorder_contractor_signature_view(request, changeorder_id):
    """Vista para capturar firma del contratista/admin en Change Orders.
    Solo accesible por staff/superuser.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff members can sign as contractor.")
    
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Calculate T&M total if applicable
    tm_breakdown = None
    if changeorder.pricing_type == 'T_AND_M':
        from core.services.financial_service import ChangeOrderService
        tm_breakdown = ChangeOrderService.get_billable_amount(changeorder)

    # Check if contractor already signed
    if changeorder.contractor_signature:
        messages.info(request, "Este Change Order ya fue firmado por el contratista.")
        return redirect("changeorder_detail", changeorder_id=changeorder.id)

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signer_name = request.POST.get("signer_name", "").strip() or request.user.get_full_name() or request.user.username

        if not signature_data:
            messages.error(request, "Por favor dibuja tu firma antes de continuar.")
            return render(
                request,
                "core/changeorder_contractor_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                },
            )

        try:
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            signature_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"contractor_sig_co_{changeorder.id}_{uuid.uuid4().hex[:8]}.{ext}",
            )

            changeorder.contractor_signature = signature_file
            changeorder.contractor_signed_by = signer_name
            changeorder.contractor_signed_at = timezone.now()
            changeorder.save(
                update_fields=[
                    "contractor_signature",
                    "contractor_signed_by",
                    "contractor_signed_at",
                ]
            )

            # Regenerate PDF if both signatures are present
            if changeorder.signature_image:
                try:
                    from core.services.pdf_service import generate_changeorder_pdf_reportlab
                    pdf_bytes = generate_changeorder_pdf_reportlab(changeorder)
                    if pdf_bytes:
                        changeorder.signed_pdf = ContentFile(
                            pdf_bytes, name=f"co_{changeorder.id}_signed.pdf"
                        )
                        changeorder.save(update_fields=["signed_pdf"])
                        
                        # Auto-save to project files
                        from core.services.document_storage_service import auto_save_signed_document
                        auto_save_signed_document(changeorder, "changeorder")
                except Exception as e:
                    logger.warning(f"Error regenerating PDF: {e}")

            messages.success(request, f"Change Order #{changeorder.id} firmado exitosamente como contratista.")
            return redirect("changeorder_detail", changeorder_id=changeorder.id)
            
        except Exception as e:
            messages.error(request, f"Error procesando la firma: {e}")
            return render(
                request,
                "core/changeorder_contractor_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                },
            )

    return render(request, "core/changeorder_contractor_signature_form.html", {
        "changeorder": changeorder,
        "tm_breakdown": tm_breakdown,
    })



@login_required
def changeorder_create_view(request):
    if not _is_staffish(request.user):
        return redirect("dashboard")
    if request.method == "POST":
        form = ChangeOrderForm(request.POST, request.FILES)
        if form.is_valid():
            co = form.save()
            
            # Handle photo uploads - optimized for faster response
            photos = request.FILES.getlist("photos")
            if photos:
                # Process photos synchronously but in a single transaction
                from django.db import transaction
                with transaction.atomic():
                    for idx, photo_file in enumerate(photos):
                        description = request.POST.get(f"photo_description_{idx}", "")
                        ChangeOrderPhoto.objects.create(
                            change_order=co, image=photo_file, description=description, order=idx
                        )
            
            # Queue background task for post-creation processing (notifications, etc.)
            try:
                from core.tasks import process_changeorder_creation
                process_changeorder_creation.delay(co.id)
            except Exception:
                pass  # Don't block if task queueing fails
            
            messages.success(request, f"Change Order #{co.id} created successfully.")
            return redirect("changeorder_board")
    else:
        form = ChangeOrderForm()

    # Get approved colors from the project if project is selected
    approved_colors = []
    project_id = request.GET.get("project")
    if project_id:
        with contextlib.suppress(Exception):
            approved_colors = ColorSample.objects.filter(
                project_id=project_id, status="approved"
            ).order_by("code")

    return render(request, "core/changeorder_form.html", {"form": form, "approved_colors": approved_colors})



@login_required
def changeorder_edit_view(request, co_id):
    """Editar un Change Order existente"""
    if not _is_staffish(request.user):
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=co_id)
    if request.method == "POST":
        form = ChangeOrderForm(request.POST, request.FILES, instance=changeorder)
        if form.is_valid():
            co = form.save()
            
            # Handle new photo uploads - optimized with transaction
            photos = request.FILES.getlist("photos")
            if photos:
                from django.db import transaction
                with transaction.atomic():
                    current_count = co.photos.count()
                    for idx, photo_file in enumerate(photos):
                        description = request.POST.get(f"photo_description_{idx}", "")
                        ChangeOrderPhoto.objects.create(
                            change_order=co,
                            image=photo_file,
                            description=description,
                            order=current_count + idx,
                        )
            
            messages.success(request, f"Change Order #{co.id} updated successfully.")
            return redirect("changeorder_board")
    else:
        form = ChangeOrderForm(instance=changeorder)

    # Get approved colors from the project
    approved_colors = ColorSample.objects.filter(
        project=changeorder.project, status="approved"
    ).order_by("code")

    return render(
        request,
        "core/changeorder_form.html",
        {
            "form": form,
            "changeorder": changeorder,
            "is_edit": True,
            "approved_colors": approved_colors,
        },
    )



@login_required
def changeorder_delete_view(request, co_id):
    """Eliminar un Change Order"""
    if not _is_staffish(request.user):
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=co_id)
    if request.method == "POST":
        changeorder.delete()
        return redirect("changeorder_board")
    return render(request, "core/changeorder_confirm_delete.html", {"changeorder": changeorder})



@login_required
def changeorder_split_view(request, co_id):
    """
    Split a Change Order: move selected time entries, expenses and photos
    from the original CO into a brand-new CO.

    Naming convention:
      - Original: CO-KPI01  → stays as-is (reference_code unchanged).
      - New split: CO-KPI01-01, CO-KPI01-02, etc.

    The new CO inherits project, pricing_type, billing rates, markup from
    the original.  Selected items are **moved** (FK re-pointed), not copied.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")

    original = get_object_or_404(ChangeOrder, id=co_id)

    # ── Gather movable items ──
    time_entries = list(
        original.time_entries.select_related("employee").order_by("-date", "-start_time")
    )
    expenses = list(original.expenses.all().order_by("-date"))
    photos = list(original.photos.all().order_by("order", "uploaded_at"))

    # ── Compute next reference code (CO-KPI01-01, -02, …) ──
    base_ref = original.reference_code or f"CO-{original.id:04d}"
    # Find existing splits: anything that starts with base_ref + "-"
    existing_splits = (
        ChangeOrder.objects.filter(
            project=original.project,
            reference_code__startswith=base_ref + "-",
        )
        .values_list("reference_code", flat=True)
    )
    max_suffix = 0
    for ref in existing_splits:
        # Extract the last segment after the base_ref
        tail = ref[len(base_ref) + 1:]  # e.g. "01", "02"
        with contextlib.suppress(ValueError):
            max_suffix = max(max_suffix, int(tail))
    next_suffix = max_suffix + 1
    next_reference_code = f"{base_ref}-{next_suffix:02d}"

    # ── POST: perform the split ──
    if request.method == "POST":
        new_ref = request.POST.get("new_reference_code", "").strip()
        new_title = request.POST.get("new_co_title", "").strip()
        new_pricing = request.POST.get("new_pricing_type", original.pricing_type)
        new_amount_raw = request.POST.get("new_amount", "0")
        new_description = request.POST.get("new_description", "").strip()

        # ── Validation ──
        errors = []
        if not new_ref:
            errors.append(_("Reference code is required."))
        if not new_title:
            errors.append(_("Title is required."))

        # Check at least one item selected
        te_ids = request.POST.getlist("time_entry_ids")
        exp_ids = request.POST.getlist("expense_ids")
        photo_ids = request.POST.getlist("photo_ids")
        if not te_ids and not exp_ids and not photo_ids:
            errors.append(_("You must select at least one item to move."))

        # Check reference code uniqueness
        if new_ref and ChangeOrder.objects.filter(reference_code=new_ref).exists():
            errors.append(_("A Change Order with reference code '%(ref)s' already exists.") % {"ref": new_ref})

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(
                request,
                "core/changeorder_split.html",
                {
                    "changeorder": original,
                    "time_entries": time_entries,
                    "expenses": expenses,
                    "photos": photos,
                    "next_reference_code": next_reference_code,
                },
            )

        # ── Parse amount ──
        try:
            from decimal import Decimal as D, InvalidOperation
            new_amount = D(new_amount_raw)
        except (InvalidOperation, ValueError):
            new_amount = Decimal("0")

        # ── Create the new CO in one atomic block ──
        from django.db import transaction

        with transaction.atomic():
            new_co = ChangeOrder.objects.create(
                project=original.project,
                co_title=new_title,
                description=new_description or original.description,
                amount=new_amount,
                pricing_type=new_pricing,
                labor_rate_override=original.labor_rate_override,
                material_markup_percent=original.material_markup_percent,
                status="draft",
                reference_code=new_ref,
                notes=_("Split from %(ref)s") % {"ref": base_ref},
                color=original.color,
            )

            # Move selected time entries
            if te_ids:
                original.time_entries.filter(id__in=te_ids).update(change_order=new_co)

            # Move selected expenses
            if exp_ids:
                original.expenses.filter(id__in=exp_ids).update(change_order=new_co)

            # Move selected photos (re-assign FK)
            if photo_ids:
                original.photos.filter(id__in=photo_ids).update(change_order=new_co)

        messages.success(
            request,
            _("Change Order split successfully. New CO: %(ref)s — %(title)s") % {
                "ref": new_ref,
                "title": new_title,
            },
        )
        return redirect("changeorder_detail", changeorder_id=new_co.id)

    # ── GET: show the split form ──
    return render(
        request,
        "core/changeorder_split.html",
        {
            "changeorder": original,
            "time_entries": time_entries,
            "expenses": expenses,
            "photos": photos,
            "next_reference_code": next_reference_code,
        },
    )



@login_required
def changeorder_board_view(request):
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    qs = ChangeOrder.objects.select_related("project").order_by("-date_created")
    status = request.GET.get("status")
    project_id = request.GET.get("project")
    if status:
        qs = qs.filter(status=status)
    if project_id:
        with contextlib.suppress(TypeError, ValueError):
            qs = qs.filter(project_id=int(project_id))
    total_amount = qs.aggregate(total=Sum("amount"))["total"] or 0
    projects = Project.objects.order_by("name")
    return render(
        request,
        "core/changeorder_board.html",
        {
            "changeorders": qs,
            "filter_status": status or "",
            "filter_project": str(project_id) if project_id else "",
            "total_amount": total_amount,
            "projects": projects,
        },
    )



# ========================================
# CHANGE ORDER API ENDPOINTS
@login_required
@require_http_methods(["PATCH"])
def changeorder_update_status(request, co_id):
    """Update Change Order status via drag and drop in board"""
    try:
        co = get_object_or_404(ChangeOrder, id=co_id)

        # Check permissions
        profile = getattr(request.user, "profile", None)
        role = getattr(profile, "role", "employee")

        if role not in ["admin", "superuser", "project_manager"]:
            return JsonResponse({"success": False, "error": "Sin permisos"}, status=403)

        # Parse request
        data = json.loads(request.body)
        new_status = data.get("status")

        # Validate status
        valid_statuses = ["pending", "approved", "sent", "billed", "paid"]
        if new_status not in valid_statuses:
            return JsonResponse({"success": False, "error": "Estado inválido"}, status=400)

        # Update status
        old_status = co.status
        co.status = new_status
        co.save()

        return JsonResponse(
            {
                "success": True,
                "co_id": co.id,
                "old_status": old_status,
                "new_status": new_status,
                "message": f"Estado actualizado a {co.get_status_display()}",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
    except Exception as e:
        logger.exception("Error updating change order status")
        return JsonResponse({"success": False, "error": "Error interno del servidor"}, status=500)



@login_required
@require_POST
def changeorder_send_to_client(request, co_id):
    """Send Change Order to client for signature"""
    try:
        co = get_object_or_404(ChangeOrder, id=co_id)

        # Check permissions
        profile = getattr(request.user, "profile", None)
        role = getattr(profile, "role", "employee")

        if role not in ["admin", "superuser", "project_manager"]:
            return JsonResponse({"success": False, "error": "Sin permisos"}, status=403)

        # Validate current status
        if co.status in ["billed", "paid"]:
            return JsonResponse(
                {"success": False, "error": "No se puede enviar un CO ya facturado o pagado"},
                status=400,
            )

        # Update status to 'sent'
        co.status = "sent"
        co.save()

        # Notify project admins/PMs about CO sent to client
        staff_users = User.objects.filter(
            is_active=True,
            profile__role__in=["admin", "project_manager"],
        ).exclude(pk=request.user.pk).distinct()
        for u in staff_users:
            Notification.objects.create(
                user=u,
                project=co.project,
                notification_type="change_order",
                title=_("Change Order #%(id)s sent to client") % {"id": co.id},
                message=_("%(user)s sent CO #%(id)s for project %(project)s to the client.") % {
                    "user": request.user.get_full_name() or request.user.username,
                    "id": co.id,
                    "project": co.project.name,
                },
                related_object_type="ChangeOrder",
                related_object_id=co.id,
                link_url=f"/changeorders/{co.id}/",
            )

        return JsonResponse(
            {
                "success": True,
                "co_id": co.id,
                "message": f"Change Order #{co.id} enviado al cliente",
                "new_status": "sent",
            }
        )

    except Exception as e:
        logger.exception("Error sending change order to client")
        return JsonResponse({"success": False, "error": "Error interno del servidor"}, status=500)



# =============================================================================
# PROFESSIONAL PDF GENERATION VIEWS
# =============================================================================

@login_required
def changeorder_pdf_download(request, changeorder_id):
    """
    Generate and download a professional PDF for a signed Change Order.
    """
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    changeorder = get_object_or_404(ChangeOrder, pk=changeorder_id)
    
    # Security check - only staff or project participants
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ChangeOrder_{changeorder.id}_{changeorder.project.project_code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('changeorder_list')



@login_required  
def changeorder_pdf_view(request, changeorder_id):
    """
    View the Change Order PDF inline in browser.
    """
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    changeorder = get_object_or_404(ChangeOrder, pk=changeorder_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ChangeOrder_{changeorder.id}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('changeorder_list')



# =============================================================================
# PUBLIC PDF DOWNLOAD VIEWS (for clients after signing)
# =============================================================================

def changeorder_public_pdf_download(request, changeorder_id, token):
    """
    Public view to download Change Order PDF after signing.
    Validates token (HMAC) with 30-day expiration.
    """
    from django.core import signing
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    changeorder = get_object_or_404(ChangeOrder, pk=changeorder_id)
    
    # Validate token
    try:
        payload = signing.loads(token, max_age=60 * 60 * 24 * 30)  # 30 days
        if payload.get("changeorder_id") != changeorder.id:
            return HttpResponseForbidden("Token does not match this Change Order.")
    except signing.SignatureExpired:
        return HttpResponseForbidden("Download link has expired. Please contact us for a new link.")
    except signing.BadSignature:
        return HttpResponseForbidden("Invalid download link.")
    
    # Check if signed
    if not changeorder.signed_at:
        return HttpResponseForbidden("This Change Order has not been signed yet.")
    
    try:
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ChangeOrder_{changeorder.id}_{changeorder.project.project_code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception(f"Error generating Change Order PDF for CO #{changeorder.id}")
        return HttpResponse("Error generating PDF. Please try again later.", status=500)


