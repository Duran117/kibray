"""Invoice, estimate, cost code & financial views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _is_staffish,
    _require_admin_or_redirect,
    _generate_basic_pdf_from_html,
    logger,
    pisa,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811



@login_required
def payroll_summary_view(request):
    """Legacy view - redirects to new payroll_weekly_review"""
    return redirect("payroll_weekly_review")


# --- INVOICES ---


@login_required
@staff_member_required
def invoice_builder_view(request, project_id):
    """
    SMART INVOICE CREATION
    - Pre-load approved Estimate items
    - Show unbilled ChangeOrders (approved/sent status, not yet billed)
    - Show unbilled TimeEntries (T&M work)
    - Generate InvoiceLines automatically
    """
    project = get_object_or_404(Project, pk=project_id)

    # Get latest approved estimate
    latest_estimate = project.estimates.filter(approved=True).order_by("-version").first()

    # Progressive billing: compute already billed percentage per estimate line
    estimate_lines_data = []
    if latest_estimate:
        from django.db.models import Sum as DJSum

        from core.models import InvoiceLineEstimate

        # Prefetch sums for efficiency
        billed_map = (
            InvoiceLineEstimate.objects.filter(estimate_line__estimate=latest_estimate)
            .values("estimate_line_id")
            .annotate(total_pct=DJSum("percentage_billed"))
        )
        billed_lookup = {row["estimate_line_id"]: (row["total_pct"] or 0) for row in billed_map}
        for line in latest_estimate.lines.select_related("cost_code").all():
            already = billed_lookup.get(line.id, 0)
            remaining = max(0, 100 - (already or 0))
            estimate_lines_data.append(
                {
                    "id": line.id,
                    "code": line.cost_code.code,
                    "description": line.description,
                    "direct_cost": line.direct_cost(),
                    "already_pct": float(already or 0),
                    "remaining_pct": float(remaining),
                }
            )

    # Unbilled ChangeOrders (ANY status except already billed/paid)
    # Shows ALL COs that haven't been invoiced yet, regardless of approval status
    unbilled_cos = (
        project.change_orders.exclude(status__in=["billed", "paid"])
        .exclude(invoices__isnull=False)
        .distinct()
    )

    # Unbilled TimeEntries (not yet linked to any invoice)
    unbilled_time = (
        TimeEntry.objects.filter(project=project, invoiceline__isnull=True)
        .select_related("employee", "change_order")
        .order_by("date")
    )

    # Group unbilled time by change_order (if any)
    time_by_co = {}
    time_general = []
    tm_hourly_rate = Decimal("50.00")  # Your rate: $50/hour

    for te in unbilled_time:
        if te.change_order:
            if te.change_order.id not in time_by_co:
                time_by_co[te.change_order.id] = {
                    "co": te.change_order,
                    "entries": [],
                    "total_hours": Decimal("0"),
                    "total_cost": Decimal("0"),
                    "billable_amount": Decimal("0"),
                }
            time_by_co[te.change_order.id]["entries"].append(te)
            time_by_co[te.change_order.id]["total_hours"] += te.hours_worked or 0
            time_by_co[te.change_order.id]["total_cost"] += te.labor_cost
        else:
            time_general.append(te)

    # Calculate billable amounts for time by CO
    for co_data in time_by_co.values():
        co_data["billable_amount"] = co_data["total_hours"] * tm_hourly_rate

    # Calculate totals for general T&M
    general_hours = sum((te.hours_worked or 0) for te in time_general)
    general_cost = sum(te.labor_cost for te in time_general)

    if request.method == "POST":
        # User selects what to include
        include_estimate = request.POST.get("include_estimate") == "on"
        selected_co_ids = request.POST.getlist("change_orders")
        include_time_general = request.POST.get("include_time_general") == "on"
        selected_time_co_ids = request.POST.getlist("time_cos")

        # Get due date
        due_date_str = request.POST.get("due_date")
        due_date = timezone.now().date() + timedelta(days=30)  # Default Net 30
        if due_date_str:
            with contextlib.suppress(Exception):
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

        # Create Invoice
        invoice = Invoice.objects.create(
            project=project,
            date_issued=timezone.now().date(),
            due_date=due_date,
            status="DRAFT",
        )

        lines_created = 0

        # Add Estimate base contract (full) or progressive portions
        if include_estimate and latest_estimate:
            # Calculate total from EstimateLines with markup
            direct_cost = sum(line.direct_cost() for line in latest_estimate.lines.all())
            material_markup = (
                direct_cost * (latest_estimate.markup_material / 100)
                if latest_estimate.markup_material
                else 0
            )
            labor_markup = (
                direct_cost * (latest_estimate.markup_labor / 100)
                if latest_estimate.markup_labor
                else 0
            )
            overhead = (
                direct_cost * (latest_estimate.overhead_pct / 100)
                if latest_estimate.overhead_pct
                else 0
            )
            profit = (
                direct_cost * (latest_estimate.target_profit_pct / 100)
                if latest_estimate.target_profit_pct
                else 0
            )
            total = direct_cost + material_markup + labor_markup + overhead + profit

            # Check if user provided progressive percentages per estimate line
            progressive_used = False
            from core.models import InvoiceLineEstimate

            for eline in latest_estimate.lines.all():
                field_name = f"prog_pct_{eline.id}"
                raw = request.POST.get(field_name)
                if not raw:
                    continue
                try:
                    pct = Decimal(raw)
                except Exception:
                    pct = Decimal("0")
                if pct <= 0:
                    continue
                # Respect remaining percentage
                # Compute already billed
                already_pct = InvoiceLineEstimate.objects.filter(estimate_line=eline).aggregate(
                    total=DJSum("percentage_billed")
                )["total"] or Decimal("0")
                remaining_pct = max(Decimal("0"), Decimal("100") - already_pct)
                if pct > remaining_pct:
                    pct = remaining_pct
                if pct <= 0:
                    continue
                progressive_used = True
                # Compute amount using direct cost proportionally (note: markups are handled in base total; here we bill direct portion)
                amount = (eline.direct_cost() or Decimal("0")) * (pct / Decimal("100"))
                il = InvoiceLine.objects.create(
                    invoice=invoice,
                    description=f"Progreso Estimado: {eline.cost_code.code} - {eline.description[:60]} ({pct}%)",
                    amount=amount,
                )
                InvoiceLineEstimate.objects.create(
                    invoice_line=il,
                    estimate_line=eline,
                    percentage_billed=pct,
                    amount=amount,
                )
                lines_created += 1

            # If no progressive input was supplied, add full base contract one-line
            if not progressive_used:
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description=f"Contrato Base - Estimado v{latest_estimate.version}",
                    amount=total,
                )
                lines_created += 1

        # Add ChangeOrders
        # Change Orders (Fixed or T&M)
        from core.services.financial_service import ChangeOrderService

        for co_id in selected_co_ids:
            try:
                co = ChangeOrder.objects.get(pk=int(co_id))
                if co.pricing_type == "FIXED":
                    InvoiceLine.objects.create(
                        invoice=invoice,
                        description=f"CO #{co.id} (Fijo): {co.description[:90]}",
                        amount=co.amount,
                    )
                    lines_created += 1
                else:
                    # T&M breakdown
                    breakdown = ChangeOrderService.get_billable_amount(co)
                    # Labor line
                    labor_line = InvoiceLine.objects.create(
                        invoice=invoice,
                        description=(
                            f"Mano de Obra CO #{co.id}: {breakdown['labor_hours']} hrs @ ${breakdown['billing_rate']}/hr"
                        ),
                        amount=breakdown["labor_total"],
                    )
                    lines_created += 1
                    # Materials line (only if there is material cost)
                    if breakdown["material_total"] > 0:
                        material_line = InvoiceLine.objects.create(
                            invoice=invoice,
                            description=(
                                f"Materiales CO #{co.id}: costo ${breakdown['raw_material_cost']} + {breakdown['material_markup_pct']}%"
                            ),
                            amount=breakdown["material_total"],
                        )
                        lines_created += 1
                    else:
                        material_line = None
                    # Mark involved entries/expenses as billed
                    for te in breakdown["time_entries"]:
                        te.invoice_line = labor_line
                        te.save(update_fields=["invoice_line"])
                    for ex in breakdown["expenses"]:
                        if material_line:
                            ex.invoice_line = material_line
                            ex.save(update_fields=["invoice_line"])
                # Mark CO billed
                co.status = "billed"
                co.save(update_fields=["status"])
                invoice.change_orders.add(co)
            except (ChangeOrder.DoesNotExist, ValueError):
                continue

        # Add Time & Materials (general - not linked to COs)
        if include_time_general and time_general:
            total_billed = general_hours * tm_hourly_rate
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f"Tiempo & Materiales - {general_hours} horas @ ${tm_hourly_rate}/hr",
                amount=total_billed,
            )
            # Link time entries to this line (optional - for tracking)
            # We'll just mark them as billed for now
            lines_created += 1

        # Add Time linked to specific COs
        for co_id_str in selected_time_co_ids:
            try:
                co_id = int(co_id_str)
                if co_id in time_by_co:
                    co_data = time_by_co[co_id]
                    co = co_data["co"]
                    hours = co_data["total_hours"]
                    total_billed = hours * tm_hourly_rate

                    InvoiceLine.objects.create(
                        invoice=invoice,
                        description=f"T&M para CO #{co.id}: {co.description[:80]} - {hours} hrs @ ${tm_hourly_rate}/hr",
                        amount=total_billed,
                    )
                    lines_created += 1
            except (ValueError, KeyError):
                pass

        # Calculate total
        invoice.total_amount = sum(line.amount for line in invoice.lines.all())
        invoice.save()

        messages.success(
            request,
            f"✅ Factura {invoice.invoice_number} creada con {lines_created} líneas. Total: ${invoice.total_amount:,.2f}",
        )
        return redirect("invoice_detail", pk=invoice.id)

    # Calculate preview totals
    estimate_total = Decimal("0")
    if latest_estimate:
        direct = sum(line.direct_cost() for line in latest_estimate.lines.all())
        estimate_total = direct * (
            1
            + (
                latest_estimate.markup_material
                + latest_estimate.markup_labor
                + latest_estimate.overhead_pct
                + latest_estimate.target_profit_pct
            )
            / 100
        )

    co_total = sum(co.amount for co in unbilled_cos)
    time_general_total = general_hours * tm_hourly_rate
    time_co_total = sum(data["total_hours"] * tm_hourly_rate for data in time_by_co.values())

    context = {
        "project": project,
        "estimate": latest_estimate,
        "estimate_lines_data": estimate_lines_data,
        "estimate_total": estimate_total,
        "unbilled_cos": unbilled_cos,
        "co_total": co_total,
        "time_general": time_general,
        "general_hours": general_hours,
        "general_cost": general_cost,
        "time_general_total": time_general_total,
        "time_by_co": time_by_co.values(),
        "time_co_total": time_co_total,
        "tm_rate": tm_hourly_rate,
        "grand_total": estimate_total + co_total + time_general_total + time_co_total,
    }
    return render(request, "core/invoice_builder.html", context)


@login_required
def invoice_list(request):
    """
    Invoice list view with filtering by status and project.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoices = (
        Invoice.objects.select_related("project")
        .prefetch_related("lines", "payments")
        .order_by("-date_issued", "-id")
    )
    
    # Apply filters
    status_filter = request.GET.get("status", "")
    project_filter = request.GET.get("project", "")
    
    if status_filter:
        if status_filter == "pending":
            # Pending = not PAID and not CANCELLED
            invoices = invoices.exclude(status__in=["PAID", "CANCELLED"])
        elif status_filter == "paid":
            invoices = invoices.filter(status="PAID")
        elif status_filter == "overdue":
            from datetime import date
            invoices = invoices.filter(
                due_date__lt=date.today()
            ).exclude(status__in=["PAID", "CANCELLED"])
        else:
            invoices = invoices.filter(status=status_filter)
    
    if project_filter:
        invoices = invoices.filter(project_id=project_filter)
    
    # Get summary stats
    from django.db.models import Sum, Count
    stats = {
        "total_count": Invoice.objects.count(),
        "draft_count": Invoice.objects.filter(status="DRAFT").count(),
        "pending_count": Invoice.objects.exclude(status__in=["PAID", "CANCELLED", "DRAFT"]).count(),
        "paid_count": Invoice.objects.filter(status="PAID").count(),
        "total_pending_amount": Invoice.objects.exclude(
            status__in=["PAID", "CANCELLED"]
        ).aggregate(total=Sum("total_amount"))["total"] or 0,
        "total_paid_amount": Invoice.objects.filter(status="PAID").aggregate(
            total=Sum("total_amount")
        )["total"] or 0,
    }
    
    projects = Project.objects.filter(is_archived=False).order_by("name")
    
    # Status choices for filter dropdown
    status_choices = Invoice.STATUS_CHOICES
    
    return render(request, "core/invoice_list.html", {
        "invoices": invoices,
        "projects": projects,
        "status_filter": status_filter,
        "project_filter": project_filter,
        "status_choices": status_choices,
        "stats": stats,
    })


@login_required
def invoice_detail(request, pk):
    """
    Modern Invoice Detail View with full financial integration.
    Shows invoice details, payment history, related COs, and actions.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(
        Invoice.objects.select_related("project")
        .prefetch_related("lines", "payments", "change_orders"),
        pk=pk
    )
    
    # Company Info (Kibray Paint & Stain LLC)
    company = {
        "name": "Kibray Paint & Stain LLC",
        "address": "P.O. Box 25881",
        "city_state_zip": "Silverthorne, CO 80497",
        "phone": "(970) 333-4872",
        "email": "jduran@kibraypainting.net",
        "website": "kibraypainting.net",
        "logo_path": "images/kibray-logo.png",
    }
    
    # Payment history
    payments = invoice.payments.all().order_by("-payment_date")
    
    # Related Change Orders
    change_orders = invoice.change_orders.all()
    
    # Calculate days until due / overdue
    days_until_due = None
    is_overdue = False
    if invoice.due_date:
        from datetime import date
        today = date.today()
        days_until_due = (invoice.due_date - today).days
        is_overdue = days_until_due < 0
    
    # Status color mapping for badges
    status_colors = {
        "DRAFT": "secondary",
        "SENT": "primary",
        "VIEWED": "info",
        "APPROVED": "success",
        "PARTIAL": "warning",
        "PAID": "success",
        "OVERDUE": "danger",
        "CANCELLED": "dark",
    }
    status_color = status_colors.get(invoice.status, "secondary")
    
    context = {
        "invoice": invoice,
        "company": company,
        "payments": payments,
        "change_orders": change_orders,
        "days_until_due": days_until_due,
        "is_overdue": is_overdue,
        "status_color": status_color,
    }
    return render(request, "core/invoice_detail.html", context)


@login_required
def invoice_pdf(request, pk):
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(Invoice, pk=pk)
    template = get_template("core/invoice_pdf.html")
    context = {
        "invoice": invoice,
        "user": request.user,
        "now": timezone.now(),  # <-- reemplazo
        "logo_url": request.build_absolute_uri("/static/kibray-logo.png"),
    }
    html = template.render(context)
    if pisa:
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type="application/pdf")
    fallback_bytes = _generate_basic_pdf_from_html(html)
    return HttpResponse(fallback_bytes, content_type="application/pdf")


@login_required
def changeorders_ajax(request):
    if not _is_staffish(request.user):
        return JsonResponse({"error": "Access denied"}, status=403)
    project_id = request.GET.get("project_id")
    status_filter = request.GET.get("status", "all")
    
    qs = ChangeOrder.objects.filter(project_id=project_id)
    
    # Filter by status if requested
    # "active" = COs where work can be tracked (excludes only 'paid')
    if status_filter == "active":
        qs = qs.filter(status__in=["draft", "pending", "approved", "sent", "billed"])
    elif status_filter != "all":
        qs = qs.filter(status=status_filter)
    
    qs = qs.order_by("-date_created")
    
    data = []
    for co in qs:
        pricing_label = "T&M" if co.pricing_type == "T_AND_M" else f"${co.amount}"
        data.append({
            "id": co.id,
            "title": co.title or f"CO #{co.id}",
            "description": co.description or "",
            "amount": float(co.amount),
            "pricing_type": co.pricing_type,
            "pricing_label": pricing_label,
            "status": co.status,
        })
    
    return JsonResponse({"change_orders": data})


@login_required
def changeorder_lines_ajax(request):
    if not _is_staffish(request.user):
        return JsonResponse({"error": "Access denied"}, status=403)
    ids = request.GET.getlist("ids[]")
    qs = ChangeOrder.objects.filter(id__in=ids)
    lines = [{"description": co.description, "amount": float(co.amount)} for co in qs]
    return JsonResponse({"lines": lines})


@login_required
def invoice_payment_dashboard(request):
    """
    Dashboard showing SENT invoices awaiting payment.
    Allows quick payment recording with check/transfer details.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    # Show invoices that are SENT, VIEWED, APPROVED, PARTIAL, or OVERDUE (not DRAFT, PAID, CANCELLED)
    pending_invoices = (
        Invoice.objects.filter(status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL", "OVERDUE"])
        .select_related("project")
        .prefetch_related("lines", "payments")
        .order_by("-date_issued")
    )

    recently_paid = (
        Invoice.objects.filter(status="PAID").select_related("project").order_by("-paid_date")[:10]
    )

    # Calculate stats for the dashboard
    overdue_count = pending_invoices.filter(status="OVERDUE").count()
    partial_count = pending_invoices.filter(status="PARTIAL").count()

    context = {
        "pending_invoices": pending_invoices,
        "recently_paid": recently_paid,
        "overdue_count": overdue_count,
        "partial_count": partial_count,
    }
    return render(request, "core/invoice_payment_dashboard.html", context)


@login_required
@transaction.atomic
def record_invoice_payment(request, invoice_id):
    """
    Quick payment recording form.
    Creates InvoicePayment, updates Invoice.amount_paid, triggers status update.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if request.method == "POST":
        amount = request.POST.get("amount")
        payment_date = request.POST.get("payment_date")
        payment_method = request.POST.get("payment_method", "CHECK")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        try:
            amount_decimal = Decimal(amount)

            # Create payment record (this auto-updates invoice via model save)
            from core.models import InvoicePayment

            InvoicePayment.objects.create(
                invoice=invoice,
                amount=amount_decimal,
                payment_date=payment_date,
                payment_method=payment_method,
                reference=reference,
                notes=notes,
                recorded_by=request.user,
            )

            messages.success(
                request,
                f"✅ Pago de ${amount_decimal:,.2f} registrado. Status: {invoice.get_status_display()}",
            )
            return redirect("invoice_payment_dashboard")

        except (ValueError, ValidationError) as e:
            messages.error(request, _("Error: %(error)s") % {"error": e})
            return redirect("invoice_detail", pk=invoice.id)

    # GET: show form
    context = {
        "invoice": invoice,
    }
    return render(request, "core/record_payment_form.html", context)


@login_required
@transaction.atomic
def invoice_mark_sent(request, invoice_id):
    """Mark invoice as SENT and record sent_date and sent_by."""
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if invoice.status == "DRAFT":
        invoice.status = "SENT"
        invoice.sent_date = timezone.now()
        invoice.sent_by = request.user
        invoice.save()
        
        # --- Auto-save PDF to Project Files ---
        try:
            from core.services.document_storage_service import auto_save_invoice_pdf
            auto_save_invoice_pdf(invoice, user=request.user, overwrite=True)
        except Exception as e:
            logger.warning(f"Failed to auto-save Invoice PDF: {e}")
        
        messages.success(
            request,
            _("✅ Factura %(invoice_number)s marcada como ENVIADA.")
            % {"invoice_number": invoice.invoice_number},
        )
    else:
        messages.warning(
            request,
            _("La factura ya tiene status: %(status)s") % {"status": invoice.get_status_display()},
        )

    return redirect("invoice_detail", pk=invoice.id)


@login_required
@transaction.atomic
def invoice_mark_approved(request, invoice_id):
    """Mark invoice as APPROVED by client."""
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if invoice.status in ["DRAFT", "SENT", "VIEWED"]:
        invoice.status = "APPROVED"
        invoice.approved_date = timezone.now()
        invoice.save()
        messages.success(
            request,
            _("✅ Factura %(invoice_number)s marcada como APROBADA.")
            % {"invoice_number": invoice.invoice_number},
        )
    else:
        messages.warning(
            request,
            _("La factura ya tiene status: %(status)s") % {"status": invoice.get_status_display()},
        )

    return redirect("invoice_detail", pk=invoice.id)


@login_required
@require_POST
@transaction.atomic
def invoice_delete(request, invoice_id):
    """
    Delete an invoice. Only allowed for DRAFT or CANCELLED invoices.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    # Only allow deletion of DRAFT or CANCELLED invoices
    if invoice.status not in ["DRAFT", "CANCELLED"]:
        messages.error(
            request,
            _("⚠️ Solo se pueden eliminar facturas en estado BORRADOR o CANCELADA. "
              "Estado actual: %(status)s") % {"status": invoice.get_status_display()},
        )
        return redirect("invoice_list")
    
    # Check if there are payments
    if invoice.payments.exists():
        messages.error(
            request,
            _("⚠️ No se puede eliminar la factura porque tiene pagos registrados."),
        )
        return redirect("invoice_detail", pk=invoice.id)
    
    invoice_number = invoice.invoice_number
    project_name = invoice.project.name
    
    # Delete related lines first
    invoice.lines.all().delete()
    
    # Delete the invoice
    invoice.delete()
    
    messages.success(
        request,
        _("✅ Factura %(invoice_number)s del proyecto %(project)s eliminada correctamente.")
        % {"invoice_number": invoice_number, "project": project_name},
    )
    
    return redirect("invoice_list")


@login_required
@require_POST
@transaction.atomic
def invoice_cancel(request, invoice_id):
    """
    Cancel an invoice. Changes status to CANCELLED.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if invoice.status == "PAID":
        messages.error(
            request,
            _("⚠️ No se puede cancelar una factura que ya está PAGADA."),
        )
        return redirect("invoice_detail", pk=invoice.id)
    
    if invoice.status == "CANCELLED":
        messages.warning(
            request,
            _("La factura ya está cancelada."),
        )
        return redirect("invoice_detail", pk=invoice.id)
    
    invoice.status = "CANCELLED"
    invoice.save()
    
    messages.success(
        request,
        _("✅ Factura %(invoice_number)s cancelada correctamente.")
        % {"invoice_number": invoice.invoice_number},
    )
    
    return redirect("invoice_detail", pk=invoice.id)


@login_required
@staff_member_required
def project_profit_dashboard(request, project_id):
    """
    Project Profit Dashboard: Real-time visibility of margins and financial health.
    Shows: Budgeted Revenue, Actual Costs, Billed Amount, Collected, Profit Margin.
    """
    project = get_object_or_404(Project, pk=project_id)

    # 1. BASE BUDGET FROM BUDGET LINES
    # Sum all baseline_amount from BudgetLine (the actual project budget)
    budget_lines_total = project.budget_lines.aggregate(
        total=Sum("baseline_amount")
    )["total"] or Decimal("0")

    # 2. ESTIMATE REVENUE (if using Estimates with markup - alternative method)
    estimate_revenue = Decimal("0")
    latest_estimate = project.estimates.filter(approved=True).order_by("-version").first()
    if latest_estimate:
        # Calculate with markup
        direct = sum(line.direct_cost() for line in latest_estimate.lines.all())
        markup_total = (
            latest_estimate.markup_material
            + latest_estimate.markup_labor
            + latest_estimate.overhead_pct
            + latest_estimate.target_profit_pct
        ) / 100
        estimate_revenue = direct * (1 + markup_total)

    # 3. CHANGE ORDERS (approved/sent, not cancelled)
    cos_revenue = project.change_orders.exclude(status__in=["cancelled", "pending"]).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    # 4. TOTAL BUDGETED REVENUE
    # Use the HIGHER of: budget_lines_total or estimate_revenue, PLUS change orders
    base_budget = max(budget_lines_total, estimate_revenue)
    budgeted_revenue = base_budget + cos_revenue

    # 5. ACTUAL COSTS (Labor + Materials/Expenses)
    # Labor cost from TimeEntries (calculated in Python since labor_cost is a property)
    time_entries = TimeEntry.objects.filter(project=project)
    labor_cost = sum(entry.labor_cost for entry in time_entries)

    # Material/Expense costs
    material_cost = Expense.objects.filter(project=project).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0")

    total_actual_cost = labor_cost + material_cost

    # 6. BILLED AMOUNT (Sum of all invoices)
    billed_amount = Invoice.objects.filter(project=project).exclude(status="CANCELLED").aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0")

    # 7. COLLECTED AMOUNT (Sum of invoice payments)
    collected_amount = Invoice.objects.filter(project=project).exclude(
        status="CANCELLED"
    ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")

    # 8. CALCULATIONS
    # Net Profit = Budgeted Revenue - Actual Costs (projected profit based on budget)
    # This shows how much profit you EXPECT to make once project is complete
    net_profit = budgeted_revenue - total_actual_cost

    # Profit Margin % = (Net Profit / Budgeted Revenue) * 100
    # Shows expected margin based on budget vs costs incurred
    margin_pct = (net_profit / budgeted_revenue * 100) if budgeted_revenue > 0 else Decimal("0")

    # Outstanding = Billed - Collected (for cash flow tracking)
    outstanding = billed_amount - collected_amount

    # Budget consumed % (how much of budget has been spent)
    budget_consumed_pct = (total_actual_cost / budgeted_revenue * 100) if budgeted_revenue > 0 else Decimal("0")
    
    # Remaining budget
    remaining_budget = budgeted_revenue - total_actual_cost

    # 9. CALCULATE PERCENTAGES FOR DISPLAY (avoid template math)
    labor_pct = (labor_cost / total_actual_cost * 100) if total_actual_cost > 0 else Decimal("0")
    material_pct = (material_cost / total_actual_cost * 100) if total_actual_cost > 0 else Decimal("0")
    collected_pct = (collected_amount / billed_amount * 100) if billed_amount > 0 else Decimal("0")
    outstanding_pct = (outstanding / billed_amount * 100) if billed_amount > 0 else Decimal("0")

    # Alert flags
    alerts = []
    if margin_pct < 10:
        alerts.append(
            {"type": "danger", "message": f"Margen crítico: {margin_pct:.1f}% (meta: >25%)"}
        )
    elif margin_pct < 25:
        alerts.append(
            {"type": "warning", "message": f"Margen bajo: {margin_pct:.1f}% (meta: >25%)"}
        )
    if outstanding > budgeted_revenue * Decimal("0.3") and outstanding > 0:
        alerts.append(
            {"type": "warning", "message": f"Alto saldo pendiente: ${outstanding:,.2f}"}
        )
    if total_actual_cost > budgeted_revenue and budgeted_revenue > 0:
        alerts.append(
            {
                "type": "danger",
                "message": f"Costos exceden presupuesto: ${total_actual_cost:,.2f} > ${budgeted_revenue:,.2f}",
            }
        )

    context = {
        "project": project,
        "budgeted_revenue": budgeted_revenue,
        "base_budget": base_budget,  # Budget Lines total or Estimate (whichever is higher)
        "budget_lines_total": budget_lines_total,  # Sum of all BudgetLine.baseline_amount
        "estimate_revenue": estimate_revenue,  # From approved Estimate with markup
        "cos_revenue": cos_revenue,
        "labor_cost": labor_cost,
        "material_cost": material_cost,
        "total_actual_cost": total_actual_cost,
        "billed_amount": billed_amount,
        "collected_amount": collected_amount,
        "outstanding": outstanding,
        "net_profit": net_profit,  # Budgeted - Costs
        "margin_pct": margin_pct,
        "budget_consumed_pct": budget_consumed_pct,
        "remaining_budget": remaining_budget,
        "labor_pct": labor_pct,
        "material_pct": material_pct,
        "collected_pct": collected_pct,
        "outstanding_pct": outstanding_pct,
        "alerts": alerts,
    }
    return render(request, "core/project_profit_dashboard.html", context)


@login_required
def costcode_list_view(request):
    """Cost Code management view with full CRUD operations."""
    if not _is_staffish(request.user):
        return redirect("dashboard")
    codes = CostCode.objects.all().order_by("category", "code")
    
    # Default categories for construction
    default_categories = [
        'Appliances', 'Cabinets', 'Cleanup', 'Concrete', 'Countertops',
        'Demolition', 'Drywall', 'Electrical', 'Equipment', 'Exterior',
        'Exterior Painting', 'Flooring', 'Framing', 'HVAC', 'Interior',
        'Interior Painting', 'Labor', 'Landscaping', 'Material', 'Plumbing',
        'Roofing', 'Subcontractor', 'Windows & Doors', 'Other',
    ]
    
    # Get existing categories normalized
    existing_raw = CostCode.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    existing_normalized = {cat.strip().title() for cat in existing_raw}
    categories = sorted(set(default_categories) | existing_normalized)
    
    if request.method == "POST":
        action = request.POST.get('action', 'create')
        
        if action == 'create':
            category = request.POST.get('category', '').strip()
            code = request.POST.get('code', '').strip().upper()
            name = request.POST.get('name', '').strip()
            active = request.POST.get('active') == 'on'
            
            if code and name:
                CostCode.objects.create(
                    code=code,
                    name=name,
                    category=category,
                    active=active
                )
                messages.success(request, _("Cost code created successfully."))
            return redirect("costcode_list")
            
        elif action == 'update':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.code = request.POST.get('code', '').strip().upper()
                    costcode.name = request.POST.get('name', '').strip()
                    costcode.category = request.POST.get('category', '').strip()
                    costcode.active = request.POST.get('active') == 'on'
                    costcode.save()
                    messages.success(request, _("Cost code updated successfully."))
                except CostCode.DoesNotExist:
                    messages.error(request, _("Cost code not found."))
            return redirect("costcode_list")
            
        elif action == 'delete':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.delete()
                    messages.success(request, _("Cost code deleted."))
                except CostCode.DoesNotExist:
                    messages.error(request, _("Cost code not found."))
            return redirect("costcode_list")
    
    return render(request, "core/costcode_list.html", {
        "codes": codes,
        "categories": categories,
    })


@login_required
@staff_member_required
def budget_lines_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = BudgetLineForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        bl = form.save(commit=False)
        bl.project = project
        bl.save()
        return redirect("budget_lines", project_id=project.id)
    lines = project.budget_lines.select_related("cost_code")
    return render(
        request, "core/budget_lines.html", {"project": project, "lines": lines, "form": form}
    )


@login_required
@staff_member_required
def estimate_create_view(request, project_id):
    
    project = get_object_or_404(Project, pk=project_id)
    version = (project.estimates.aggregate(m=Max("version"))["m"] or 0) + 1
    cost_codes = CostCode.objects.all().order_by("code")
    
    if request.method == "POST":
        form = EstimateForm(request.POST)
        formset = EstimateLineFormSet(request.POST, prefix='lines')
        
        logger.info(f"Estimate form POST received for project {project_id}")
        logger.info(f"Form valid: {form.is_valid()}")
        logger.info(f"Formset valid: {formset.is_valid()}")
        
        if not form.is_valid():
            logger.warning(f"Form errors: {form.errors}")
            messages.error(request, _("Please correct the errors in the form."))
            
        if not formset.is_valid():
            logger.warning(f"Formset errors: {formset.errors}")
            # Count non-empty lines that have errors
            line_errors = [e for e in formset.errors if e]
            if line_errors:
                messages.error(request, _("Please correct the errors in the line items."))
        
        if form.is_valid() and formset.is_valid():
            est = form.save(commit=False)
            est.project = project
            est.version = version
            est.save()
            formset.instance = est
            
            # Save lines and filter out empty ones
            saved_lines = []
            for line_form in formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                    if line_form.cleaned_data.get('cost_code'):
                        line = line_form.save(commit=False)
                        line.estimate = est
                        line.save()
                        saved_lines.append(line)
            
            logger.info(f"Created Estimate {est.code} with {len(saved_lines)} lines")
            messages.success(request, _("Estimate created successfully! You can now send it to the client for approval."))
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        form = EstimateForm()
        formset = EstimateLineFormSet(prefix='lines')
    
    return render(
        request,
        "core/estimate_form.html",
        {
            "project": project,
            "form": form,
            "formset": formset,
            "version": version,
            "cost_codes": cost_codes,
        },
    )


@login_required
def estimate_edit_view(request, estimate_id):
    """Edit an existing estimate."""
    
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = estimate.project
    cost_codes = CostCode.objects.all().order_by("code")
    
    # Prevent editing approved estimates
    if estimate.approved:
        messages.warning(request, _("This estimate has been approved and cannot be edited."))
        return redirect("estimate_detail", estimate_id=estimate.id)
    
    if request.method == "POST":
        form = EstimateForm(request.POST, instance=estimate)
        formset = EstimateLineFormSet(request.POST, instance=estimate, prefix='lines')
        
        logger.info(f"Estimate edit POST received for estimate {estimate_id}")
        logger.info(f"Form valid: {form.is_valid()}")
        logger.info(f"Formset valid: {formset.is_valid()}")
        
        if not form.is_valid():
            logger.warning(f"Form errors: {form.errors}")
            messages.error(request, _("Please correct the errors in the form."))
            
        if not formset.is_valid():
            logger.warning(f"Formset errors: {formset.errors}")
            line_errors = [e for e in formset.errors if e]
            if line_errors:
                messages.error(request, _("Please correct the errors in the line items."))
        
        if form.is_valid() and formset.is_valid():
            est = form.save()
            
            # Save lines
            saved_lines = []
            for line_form in formset:
                if line_form.cleaned_data:
                    if line_form.cleaned_data.get('DELETE', False):
                        if line_form.instance.pk:
                            line_form.instance.delete()
                    elif line_form.cleaned_data.get('cost_code'):
                        line = line_form.save(commit=False)
                        line.estimate = est
                        line.save()
                        saved_lines.append(line)
            
            logger.info(f"Updated Estimate {est.code} with {len(saved_lines)} lines")
            messages.success(request, _("Estimate updated successfully!"))
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        form = EstimateForm(instance=estimate)
        formset = EstimateLineFormSet(instance=estimate, prefix='lines')
    
    return render(
        request,
        "core/estimate_form.html",
        {
            "project": project,
            "form": form,
            "formset": formset,
            "estimate": estimate,
            "version": estimate.version,
            "cost_codes": cost_codes,
            "is_edit": True,
        },
    )


@login_required
def estimate_detail_view(request, estimate_id):
    
    est = get_object_or_404(Estimate, pk=estimate_id)
    
    # SECURITY: Only staff/superusers can view estimates (financial data)
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    
    # Handle manual approval action
    if request.method == "POST" and request.POST.get("action") == "approve_manual":
        if not est.approved:
            from decimal import Decimal
            
            est.approved = True
            est.save(update_fields=["approved"])
            
            # Auto-create Budget Lines
            try:
                from core.services.budget_from_estimate import create_budget_from_estimate
                profit_margin = est.target_profit_pct / Decimal("100") if est.target_profit_pct else None
                budget_lines = create_budget_from_estimate(est, profit_margin=profit_margin)
                logger.info(f"Created {len(budget_lines)} budget lines for manually approved Estimate {est.code}")
                messages.success(request, _(f"Estimate approved! {len(budget_lines)} budget lines created with profit margin deducted."))
            except Exception as e:
                logger.error(f"Failed to create budget lines: {e}")
                messages.warning(request, _("Estimate approved but failed to create budget lines automatically."))
            
            # Auto-create Contract with new professional format
            try:
                from core.services.contract_service import ContractService
                # Create contract but defer PDF generation to background task to keep UI responsive
                contract = ContractService.create_contract_from_estimate(
                    estimate=est,
                    user=request.user,
                    auto_generate_pdf=False,
                )
                # Queue background job to generate and save the professional PDF
                try:
                    from core.tasks import process_contract_generation

                    process_contract_generation.delay(contract.id, request.user.id)
                    messages.info(request, _("Contract created. PDF generation queued in background."))
                except Exception:
                    # If task queue isn't available, fallback to synchronous generation (best-effort)
                    try:
                        ContractService.generate_contract_pdf(contract, request.user)
                        messages.info(request, _("Contract created and PDF generated."))
                    except Exception as e:
                        logger.warning(f"Contract PDF generation failed (fallback): {e}")
                        messages.info(request, _("Contract created but PDF generation failed; you can regenerate later."))
                logger.info(f"Created contract {getattr(contract, 'contract_number', 'N/A')} for estimate {est.code}")
            except ValueError as ve:
                # Contract already exists - just regenerate PDF
                if hasattr(est, 'contract') and est.contract:
                    ContractService.generate_contract_pdf(est.contract, request.user)
                    messages.info(request, _("Contract PDF regenerated."))
                else:
                    logger.warning(f"Contract creation error: {ve}")
            except Exception as e:
                logger.warning(f"Failed to create contract: {e}")
                # Fallback to old PDF generation
                from core.services.document_storage_service import auto_save_estimate_pdf
                auto_save_estimate_pdf(est, user=request.user, as_contract=True, overwrite=True)
                messages.info(request, _("Contract PDF saved to project documents (legacy format)."))
        else:
            messages.info(request, _("Estimate was already approved."))
        
        return redirect("estimate_detail", estimate_id=est.id)
    
    # Handle regenerate PDF action
    if request.method == "POST" and request.POST.get("action") == "regenerate_pdf":
        try:
            if est.approved:
                # Use new Contract system for approved estimates
                from core.services.contract_service import ContractService
                
                # Get or create contract
                if hasattr(est, 'contract') and est.contract:
                    contract = est.contract
                else:
                    # Create contract if doesn't exist (for legacy approved estimates)
                    contract = ContractService.create_contract_from_estimate(
                        estimate=est,
                        user=request.user,
                        auto_generate_pdf=False,
                    )

                # Queue background regeneration of the PDF to avoid blocking the request
                try:
                    from core.tasks import process_contract_generation

                    process_contract_generation.delay(contract.id, request.user.id, True)
                    messages.success(request, _("Contract PDF regeneration queued in background."))
                except Exception:
                    # Fallback to synchronous regeneration if task queue isn't available
                    try:
                        result = ContractService.generate_contract_pdf(contract, request.user)
                        if result:
                            messages.success(request, _("Contract PDF regenerated successfully with professional format!"))
                        else:
                            messages.error(request, _("Failed to regenerate contract PDF."))
                    except Exception as e:
                        logger.error(f"Failed to regenerate PDF (fallback): {e}")
                        messages.error(request, _(f"Error: {str(e)}"))
            else:
                # For non-approved estimates, use regular estimate PDF
                from core.services.document_storage_service import auto_save_estimate_pdf
                result = auto_save_estimate_pdf(est, user=request.user, as_contract=False, overwrite=True)
                if result:
                    messages.success(request, _("Estimate PDF regenerated successfully!"))
                else:
                    messages.error(request, _("Failed to regenerate PDF."))
        except Exception as e:
            logger.error(f"Failed to regenerate PDF: {e}")
            messages.error(request, _(f"Error: {str(e)}"))
        
        return redirect("estimate_detail", estimate_id=est.id)
    
    lines = est.lines.select_related("cost_code")
    direct = sum(line.direct_cost() for line in lines)
    material_markup = direct * (est.markup_material / 100)
    labor_markup = direct * (est.markup_labor / 100)
    overhead = direct * (est.overhead_pct / 100)
    target_profit = direct * (est.target_profit_pct / 100)
    proposed_price = direct + material_markup + labor_markup + overhead + target_profit
    
    # Get budget preview if not yet approved
    budget_preview = None
    if not est.approved:
        try:
            from core.services.budget_from_estimate import get_estimate_to_budget_summary
            budget_preview = get_estimate_to_budget_summary(est)
        except Exception:
            pass
    
    return render(
        request,
        "core/estimate_detail.html",
        {
            "estimate": est,
            "lines": lines,
            "direct": direct,
            "proposed_price": proposed_price,
            "budget_preview": budget_preview,
        },
    )


@login_required
def estimate_send_email(request, estimate_id):
    """Vista para pre-editar y enviar la propuesta al cliente por email.

    GET: retorna fragmento HTML con formulario pre-llenado (para cargar en modal).
    POST: envía el correo y redirige al detalle del estimate con mensaje de éxito.
    """
    # SECURITY: Only staff/superusers can send estimates
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    
    import uuid

    from django.conf import settings
    from django.utils import timezone

    est = get_object_or_404(Estimate, pk=estimate_id)
    # Asegurar Proposal y token
    from core.models import Proposal

    proposal, created = Proposal.objects.get_or_create(
        estimate=est,
        defaults={"issued_at": timezone.now()},
    )
    if not proposal.client_view_token:
        proposal.client_view_token = uuid.uuid4()
        proposal.save(update_fields=["client_view_token"])

    public_url = request.build_absolute_uri(
        reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
    )

    # Heurística para pre-llenar email del cliente
    initial_recipient = None
    if est.project.client and "@" in est.project.client:
        initial_recipient = est.project.client.strip()
    else:
        try:
            from core.models import ClientProjectAccess

            cpa = (
                ClientProjectAccess.objects.filter(project=est.project, role="client")
                .select_related("user")
                .first()
            )
            if cpa and cpa.user and cpa.user.email:
                initial_recipient = cpa.user.email
        except Exception:
            pass

    if request.method == "POST":
        form = ProposalEmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            recipient = form.cleaned_data["recipient"]
            # Garantizar que el link está incluido
            if public_url not in message:
                message = f"{message}\n\nVer y aprobar la cotización:\n{public_url}"
            sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
            error_msg = None
            success_flag = True
            try:
                # Construir versión HTML simple
                html_body = (
                    "<p>"
                    + message.replace("\n\n", "</p><p>").replace("\n", "<br>")
                    + "</p>"
                    + f"<p><a href='{public_url}' style='display:inline-block;padding:12px 20px;background:#4CAF50;color:#fff;text-decoration:none;border-radius:6px;'>Ver y Aprobar Cotización</a></p>"
                )
                from core.services.email_service import KibrayEmailService
                KibrayEmailService.send_html_email(
                    to_email=recipient,
                    subject=subject,
                    text_content=message,
                    html_content=html_body,
                    fail_silently=False
                )
                messages.success(request, "Propuesta enviada correctamente al cliente.")
            except Exception as e:
                success_flag = False
                error_msg = str(e)
                messages.error(request, _("Error enviando correo: %(error)s") % {"error": e})

            # Log persistente
            from core.models import ProposalEmailLog

            with contextlib.suppress(Exception):
                ProposalEmailLog.objects.create(
                    proposal=proposal,
                    estimate=est,
                    recipient=recipient,
                    subject=subject,
                    message_preview=message[:500],
                    success=success_flag,
                    error_message=error_msg,
                )
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        client_name = est.project.client or "Cliente"
        subject = f"Cotización {getattr(est, 'code', '')} - {est.project.name}".strip()
        message = (
            f"Hola {client_name},\n\n"
            "Adjunto encontrarás la cotización detallada para tu revisión.\n\n"
            f"Puedes verla y aprobarla aquí:\n{public_url}\n\n"
            "Saludos,\nTu Empresa"
        )
        form = ProposalEmailForm(
            initial={
                "subject": subject,
                "message": message,
                "recipient": initial_recipient or "",
            }
        )

    # GET -> retornar fragmento para modal (o página completa si se accede directamente)
    template_name = (
        "core/partials/proposal_email_form.html"
        if request.headers.get("Hx-Request") or request.GET.get("partial")
        else "core/partials/proposal_email_form.html"
    )
    return render(
        request,
        template_name,
        {
            "form": form,
            "estimate": est,
            "public_url": public_url,
        },
    )


