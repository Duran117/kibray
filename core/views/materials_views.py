"""Materials, inventory & supply chain views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _is_staffish,
    _require_admin_or_redirect,
    _ensure_inventory_item,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


@login_required
def materials_request_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    try:
        from core.models import Color

        colors = Color.objects.filter(project=project).order_by("name")
    except Exception:
        colors = []

    catalog_qs = (
        MaterialCatalog.objects.filter(is_active=True)
        .filter(Q(project=project) | Q(project__isnull=True))
        .order_by("brand_text", "product_name")
    )

    if request.method == "POST":
        form = MaterialsRequestForm(
            request.POST, request.FILES, colors=colors, presets=PRESET_PRODUCTS, catalog=catalog_qs
        )
        if form.is_valid():
            # Get activity information from query parameters or POST
            activity_id = request.GET.get("activity_id") or request.POST.get("activity_id")
            activity_name = request.GET.get("activity_name", "") or request.POST.get(
                "activity_name", ""
            )

            # Build notes with activity reference
            notes = form.cleaned_data.get("comments", "")
            if activity_id and activity_name:
                activity_note = f"[Solicitado para actividad: {activity_name} (ID: {activity_id})]"
                notes = f"{activity_note}\n{notes}" if notes else activity_note

            mr = MaterialRequest.objects.create(
                project=project,
                requested_by=request.user,
                needed_when=form.cleaned_data["needed_when"],
                needed_date=form.cleaned_data.get("needed_date") or None,
                notes=notes,
                status="pending",
            )

            # 1) Si eligió un ítem del catálogo, precargar
            selected = form.cleaned_data.get("catalog_item")
            cat_data = None
            if selected:
                try:
                    mc = catalog_qs.get(id=int(selected))
                    cat_data = {
                        "category": mc.category,
                        "brand_text": mc.brand_text,
                        "product_name": mc.product_name,
                        "color_name": mc.color_name,
                        "color_code": mc.color_code,
                        "finish": mc.finish,
                        "gloss": mc.gloss,
                        "formula": mc.formula,
                        "default_unit": mc.default_unit,
                    }
                except Exception:
                    pass

            # 2) Datos del formulario (manual/preset/color aprobado)
            cleaned = form.cleaned_data
            category = cleaned["category"]
            brand_choice = cleaned["brand"]
            brand_text = dict(MaterialRequestItem.BRAND_CHOICES).get(brand_choice, brand_choice)
            if brand_choice == "other" and cleaned.get("brand_other"):
                brand_text = cleaned["brand_other"]

            product_name = cleaned["product_name"]
            color_name = cleaned["color_name"]
            color_code = cleaned["color_code"]
            finish = cleaned["finish"]
            gloss = cleaned["gloss"]
            formula = cleaned["formula"]
            unit = cleaned["unit"]

            # Aplicar preset si se eligió (solo completa vacíos)
            preset_idx = cleaned.get("product_preset")
            if preset_idx:
                try:
                    p = PRESET_PRODUCTS[int(preset_idx)]
                    category = category or p["category"]
                    if not product_name:
                        product_name = p["product_name"]
                    if unit in ("", None):
                        unit = p.get("unit") or unit
                    if not brand_text or brand_choice != "other":
                        brand_text = p["brand_label"]
                except Exception:
                    pass

            # Aplicar color aprobado si se eligió (solo completa vacíos)
            approved_id = cleaned.get("approved_color")
            if approved_id and colors:
                try:
                    c = colors.get(id=int(approved_id))
                    brand_text = getattr(c, "brand", brand_text) or brand_text
                    product_name = getattr(c, "line", product_name) or product_name
                    color_name = getattr(c, "name", color_name) or color_name
                    color_code = getattr(c, "code", color_code) or color_code
                    finish = getattr(c, "finish", finish) or finish
                    gloss = getattr(c, "gloss", gloss) or gloss
                    formula = getattr(c, "formula", formula) or formula
                except Exception:
                    pass

            # Si viene del catálogo, sobrescribir con sus valores
            if cat_data:
                category = cat_data["category"]
                brand_text = cat_data["brand_text"]
                product_name = cat_data["product_name"] or product_name
                color_name = cat_data["color_name"] or color_name
                color_code = cat_data["color_code"] or color_code
                finish = cat_data["finish"] or finish
                gloss = cat_data["gloss"] or gloss
                formula = cat_data["formula"] or formula
                unit = cat_data["default_unit"] or unit

            # Crear ítem solicitado
            extra_comments = cleaned.get("comments", "")
            if brand_choice == "other" and cleaned.get("brand_other"):
                extra_comments = f"Marca especificada: {cleaned['brand_other']}. " + extra_comments

            MaterialRequestItem.objects.create(
                request=mr,
                category=category,
                brand=cleaned["brand"],  # guardamos la clave de choice para el item
                product_name=product_name,
                color_name=color_name,
                color_code=color_code,
                finish=finish,
                gloss=gloss,
                formula=form.cleaned_data["formula"] or formula,
                reference_image=form.cleaned_data.get("reference_image"),
                quantity=cleaned["quantity"],
                qty_requested=cleaned["quantity"],
                unit=unit,
                comments=extra_comments,
            )

            # Guardar en catálogo si se indicó (scoped al proyecto)
            if cleaned.get("save_to_catalog"):
                MaterialCatalog.objects.get_or_create(
                    project=project,
                    category=category,
                    brand_text=brand_text or "",
                    product_name=product_name or "",
                    color_name=color_name or "",
                    color_code=color_code or "",
                    finish=finish or "",
                    defaults={
                        "gloss": gloss or "",
                        "formula": formula or "",
                        "default_unit": unit or "",
                        "created_by": request.user,
                    },
                )

            messages.success(
                request,
                (
                    "Solicitud registrada. El material quedó guardado en el catálogo del proyecto."
                    if cleaned.get("save_to_catalog")
                    else "Solicitud registrada."
                ),
            )
            return redirect(reverse("materials_request", args=[project.id]))

    else:
        form = MaterialsRequestForm(colors=colors, presets=PRESET_PRODUCTS, catalog=catalog_qs)

    catalog_payload = [
        {
            "id": m.id,
            "category": m.category,
            "brand_text": m.brand_text,
            "product_name": m.product_name,
            "color_name": m.color_name,
            "color_code": m.color_code,
            "finish": m.finish,
            "gloss": m.gloss,
            "formula": m.formula,
            "default_unit": m.default_unit,
        }
        for m in catalog_qs
    ]

    # Get activity information from query parameters
    activity_id = request.GET.get("activity_id")
    activity_name = request.GET.get("activity_name", "")

    return render(
        request,
        "core/materials_request.html",
        {
            "project": project,
            "form": form,
            "presets_json": json.dumps(PRESET_PRODUCTS),
            "catalog_json": json.dumps(catalog_payload),
            "activity_id": activity_id,
            "activity_name": activity_name,
        },
    )


@login_required


@login_required
def inventory_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    storage = InventoryLocation.objects.filter(is_storage=True).first()
    loc, __ = InventoryLocation.objects.get_or_create(
        project=project, name="Principal", defaults={"is_storage": False}
    )
    stocks = (
        ProjectInventory.objects.filter(location=loc)
        .select_related("item")
        .order_by("item__category", "item__name")
    )
    low = [s for s in stocks if s.is_below]  # <- propiedad, sin paréntesis
    return render(
        request,
        "core/inventory_view.html",
        {
            "project": project,
            "stocks": stocks,
            "low": low,
            "storage": storage,
        },
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def inventory_move_view(request, project_id):
    from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

    project = get_object_or_404(Project, pk=project_id)

    # Asegurar storage y ubicación principal del proyecto actual
    storage = InventoryLocation.objects.filter(is_storage=True).first()
    if not storage:
        storage = InventoryLocation.objects.create(name="Main Storage", is_storage=True)
    proj_loc, __ = InventoryLocation.objects.get_or_create(
        project=project, name="Principal", defaults={"is_storage": False}
    )

    form = InventoryMovementForm(request.POST or None)

    # Desde: solo storage o ubicaciones del proyecto actual
    from_qs = InventoryLocation.objects.filter(Q(is_storage=True) | Q(project=project)).order_by(
        "-is_storage", "name"
    )
    # Hacia: storage o cualquier ubicación de cualquier proyecto (permite transferir a otro proyecto)
    to_qs = InventoryLocation.objects.filter(
        Q(is_storage=True) | Q(project__isnull=False)
    ).order_by("-is_storage", "project__name", "name")

    form.fields["from_location"].queryset = from_qs
    form.fields["to_location"].queryset = to_qs
    form.fields["item"].queryset = InventoryItem.objects.filter(active=True).order_by(
        "category", "name"
    )

    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["item"]
        mtype = form.cleaned_data["movement_type"]
        qty = form.cleaned_data["quantity"]
        from_loc = form.cleaned_data.get("from_location")
        to_loc = form.cleaned_data.get("to_location")
        note = form.cleaned_data.get("note") or ""

        # Validar requeridos según tipo
        if mtype in ("RECEIVE", "RETURN") and not to_loc:
            form.add_error("to_location", "Requerido.")
        if mtype in ("ISSUE", "CONSUME", "TRANSFER") and not from_loc:
            form.add_error("from_location", "Requerido.")

        # Validar stock en origen para salidas/traslados
        if not form.errors and mtype in ("ISSUE", "CONSUME", "TRANSFER"):
            stock = ProjectInventory.objects.filter(item=item, location=from_loc).first()
            if not stock or stock.quantity < qty:
                form.add_error(
                    "quantity",
                    f"Stock insuficiente en origen (disp: {float(stock.quantity) if stock else 0}).",
                )

        if not form.errors:
            move = InventoryMovement.objects.create(
                item=item,
                movement_type=mtype,
                quantity=qty,
                from_location=from_loc,
                to_location=to_loc,
                note=note,
                created_by=request.user,
            )
            move.apply()
            # Decidir siguiente paso
            if form.cleaned_data.get("add_expense"):
                next_url = reverse("inventory_history", args=[project.id])
                create_url = f"{reverse('expense_create')}?project_id={project.id}&next={next_url}&ref=inv_move_{move.id}"
                messages.info(request, _("Ahora registra el gasto del ticket."))
                return redirect(create_url)
            if form.cleaned_data.get("no_expense"):
                messages.success(request, _("Movimiento aplicado. Marcado sin gasto."))
                return redirect("inventory_view", project_id=project.id)

            messages.success(request, _("Movimiento aplicado."))
            return redirect("inventory_view", project_id=project.id)
    return render(request, "core/inventory_move.html", {"project": project, "form": form})


@login_required
@staff_required
def inventory_history_view(request, project_id):
    from core.models import InventoryItem, InventoryLocation, InventoryMovement

    project = get_object_or_404(Project, pk=project_id)
    loc_qs = InventoryLocation.objects.filter(Q(project=project) | Q(is_storage=True))
    item_id = request.GET.get("item")
    mtype = request.GET.get("type")
    qs = (
        InventoryMovement.objects.filter(Q(from_location__in=loc_qs) | Q(to_location__in=loc_qs))
        .select_related("item", "from_location", "to_location", "created_by")
        .order_by("-created_at", "-id")
    )
    if item_id:
        qs = qs.filter(item_id=item_id)
    if mtype:
        qs = qs.filter(movement_type=mtype)

    items = InventoryItem.objects.filter(active=True).order_by("category", "name")
    return render(
        request,
        "core/inventory_history.html",
        {
            "project": project,
            "moves": qs[:200],
            "items": items,
            "current_item": int(item_id) if item_id else "",
            "current_type": mtype or "",
        },
    )


@login_required
@staff_required
def materials_receive_ticket_view(request, request_id):
    """
    Pantalla para recibir/comprar un lote (ticket) de ítems de la solicitud.
    Genera un Expense (si aplica) + movimientos RECEIVE por cada ítem seleccionado.
    """
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    project = mat_request.project

    # Import here to ensure InventoryMovement is available in this scope
    from core.models import InventoryMovement

    if request.method == "POST":
        # Campos gasto
        store_name = request.POST.get("store_name", "").strip()
        total = request.POST.get("total", "0").strip()
        no_expense = request.POST.get("no_expense") == "on"
        receipt_photo = request.FILES.get("receipt_photo")

        # Items recibidos
        items_data = []
        for item in mat_request.items.all():
            checked = request.POST.get(f"item_{item.id}") == "on"
            qty = request.POST.get(f"qty_{item.id}", "0").strip()
            if checked:
                try:
                    # Clean thousands separators and convert string -> Decimal
                    q = qty.replace(",", "") if isinstance(qty, str) else qty
                    q_dec = Decimal(q) if q not in (None, "", " ") else Decimal("0")
                    if q_dec > 0:
                        items_data.append((item, q_dec))
                except Exception:
                    pass

        # Validar
        if not items_data:
            messages.error(request, _("Selecciona al menos un ítem con cantidad > 0."))
            return redirect("materials_receive_ticket", request_id=mat_request.id)

        if not no_expense and (not store_name or not total or Decimal(total) <= 0):
            messages.error(request, _("Completa tienda y total o marca 'Sin gasto'."))
            return redirect("materials_receive_ticket", request_id=mat_request.id)

        # Crear Expense (si aplica)
        expense_obj = None
        if not no_expense:
            expense_obj = Expense.objects.create(
                project=project,
                project_name=f"{project.name} - {store_name}",
                category="MATERIALES",
                amount=Decimal(total),
                description=f"Ticket {store_name} - {mat_request.id}",
                receipt=receipt_photo,
                date=timezone.now().date(),
            )

        # Asegurar ubicación Principal del proyecto
        loc, __ = InventoryLocation.objects.get_or_create(
            project=project, name="Principal", defaults={"is_storage": False}
        )

        # Crear movimientos RECEIVE y actualizar ítems
        with transaction.atomic():
            for item, qty in items_data:
                # Asegurar InventoryItem (auto-crear si no existe)
                if not item.inventory_item:
                    inv_item = _ensure_inventory_item(
                        name=item.product_name or "Item",
                        category_key=item.category or "MATERIAL",
                        unit=item.unit or "pcs",
                    )
                    item.inventory_item = inv_item
                    item.save(update_fields=["inventory_item"])

                # Crear movimiento RECEIVE
                move = InventoryMovement.objects.create(
                    item=item.inventory_item,
                    movement_type="RECEIVE",
                    quantity=qty,
                    to_location=loc,
                    note=f"Ticket {store_name} - Solicitud {mat_request.id}",
                    created_by=request.user,
                    expense=expense_obj,
                )
                move.apply()

                # Actualizar ítem de solicitud
                item.qty_received += qty
                if item.qty_received >= item.qty_requested:
                    item.item_status = "received"
                else:
                    item.item_status = "received_partial"
                item.save(update_fields=["qty_received", "item_status"])

        messages.success(
            request,
            _("Ticket procesado. %(count)s ítem(s) recibido(s).") % {"count": len(items_data)},
        )
        return redirect("materials_request_detail", request_id=mat_request.id)

    # GET: mostrar checklist
    items = mat_request.items.all()
    return render(
        request,
        "core/materials_receive_ticket.html",
        {
            "mat_request": mat_request,
            "project": project,
            "items": items,
        },
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def materials_direct_purchase_view(request, project_id):
    """
    Compra directa del lead: registra ítems comprados, crea solicitud retroactiva
    con status 'purchased_lead', movimientos RECEIVE y Expense.
    """
    project = get_object_or_404(Project, pk=project_id)

    from core.models import InventoryMovement

    if request.method == "POST":
        # Datos del ticket
        store_name = request.POST.get("store_name", "").strip()
        total = request.POST.get("total", "0").strip()
        no_expense = request.POST.get("no_expense") == "on"
        receipt_photo = request.FILES.get("receipt_photo")
        notes = request.POST.get("notes", "").strip()

        # Items comprados (JSON enviado desde JS o form dinámico)
        # Formato esperado: [{"name": "Tape 2in", "category": "tape", "unit": "roll", "qty": 36}, ...]
        import json

        items_json = request.POST.get("items_json", "[]")
        try:
            items_data = json.loads(items_json)
        except Exception:
            items_data = []

        # Validar
        if not items_data:
            messages.error(request, _("Agrega al menos un ítem con cantidad > 0."))
            return redirect("materials_direct_purchase", project_id=project.id)

        if not no_expense and (not store_name or not total or Decimal(total) <= 0):
            messages.error(request, _("Completa tienda y total o marca 'Sin gasto'."))
            return redirect("materials_direct_purchase", project_id=project.id)

        # Crear Expense (si aplica)
        expense_obj = None
        if not no_expense:
            expense_obj = Expense.objects.create(
                project=project,
                project_name=f"{project.name} - {store_name}",
                category="MATERIALES",
                amount=Decimal(total),
                description=f"Compra directa {store_name}",
                receipt=receipt_photo,
                date=timezone.now().date(),
            )

        # Crear MaterialRequest retroactiva
        mat_request = MaterialRequest.objects.create(
            project=project,
            requested_by=request.user,
            status="purchased_lead",
            notes=notes or f"Compra directa en {store_name}",
        )

        # Asegurar ubicación Principal del proyecto
        loc, __ = InventoryLocation.objects.get_or_create(
            project=project, name="Principal", defaults={"is_storage": False}
        )

        # Crear ítems + movimientos RECEIVE
        with transaction.atomic():
            for item_data in items_data:
                name = item_data.get("name", "").strip()
                category = item_data.get("category", "MATERIAL")
                unit = item_data.get("unit", "pcs")
                qty = Decimal(item_data.get("qty", 0))

                if not name or qty <= 0:
                    continue

                # Asegurar InventoryItem
                inv_item = _ensure_inventory_item(name=name, category_key=category, unit=unit)

                # Crear ítem de solicitud
                MaterialRequestItem.objects.create(
                    request=mat_request,
                    inventory_item=inv_item,
                    product_name=name,
                    category=category,
                    unit=unit,
                    quantity=qty,
                    qty_requested=qty,
                    qty_received=qty,
                    item_status="received",
                )

                # Crear movimiento RECEIVE
                move = InventoryMovement.objects.create(
                    item=inv_item,
                    movement_type="RECEIVE",
                    quantity=qty,
                    to_location=loc,
                    note=f"Compra directa {store_name} - Solicitud {mat_request.id}",
                    created_by=request.user,
                    expense=expense_obj,
                )
                move.apply()

        messages.success(
            request,
            _("Compra directa registrada. %(count)s ítem(s) agregado(s) al inventario.")
            % {"count": len(items_data)},
        )
        return redirect("inventory_view", project_id=project.id)

    # GET: mostrar formulario dinámico
    return render(request, "core/materials_direct_purchase.html", {"project": project})


@login_required
@staff_required
def materials_requests_list_view(request, project_id=None):
    """
    Lista todas las solicitudes de materiales con acciones:
    - Ver detalle
    - Marcar como 'ordered'
    - Crear ticket (receive)
    """
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        qs = MaterialRequest.objects.filter(project=project)
    else:
        project = None
        qs = MaterialRequest.objects.all()

    # Filtros
    status_filter = request.GET.get("status", "")
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = (
        qs.select_related("project", "requested_by")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "core/materials_requests_list.html",
        {
            "project": project,
            "requests": qs,
            "status_filter": status_filter,
            "status_choices": MaterialRequest.STATUS_CHOICES,
        },
    )


@login_required
@staff_required
@require_POST
def materials_mark_ordered_view(request, request_id):
    """
    Cambia status de solicitud a 'ordered'.
    """
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    mat_request.status = "ordered"
    mat_request.save(update_fields=["status"])

    mat_request.items.filter(item_status="pending").update(item_status="ordered")

    messages.success(
        request, _("Solicitud #%(id)s marcada como ordenada.") % {"id": mat_request.id}
    )
    return redirect("materials_requests_list", project_id=mat_request.project_id)


@login_required
@staff_required
@require_POST
def materials_request_delete_view(request, request_id):
    """
    Elimina una solicitud de materiales (solo staff/admin).
    """
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    project_id = mat_request.project_id
    req_id = mat_request.id
    
    # Delete the request (items will be deleted via CASCADE)
    mat_request.delete()
    
    messages.success(
        request, _("Solicitud #%(id)s eliminada correctamente.") % {"id": req_id}
    )
    
    if project_id:
        return redirect("materials_requests_list", project_id=project_id)
    return redirect("materials_requests_list_all")


@login_required
def materials_request_detail_view(request, request_id):
    """
    Muestra detalle de solicitud con ítems.
    """
    mat_request = get_object_or_404(
        MaterialRequest.objects.select_related("project", "requested_by"), pk=request_id
    )
    items = mat_request.items.select_related("inventory_item").all()

    can_manage = _is_staffish(request.user)

    return render(
        request,
        "core/materials_request_detail.html",
        {
            "mat_request": mat_request,
            "items": items,
            "can_manage": can_manage,
        },
    )


# ===========================
# ACTIVITY 2: NEW MATERIAL REQUEST WORKFLOW VIEWS
# ===========================


@login_required
@require_POST
def materials_request_submit(request, request_id):
    """Q14.4: Enviar solicitud para aprobación del admin"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    # Verify user can submit
    if mat_request.requested_by != request.user and not request.user.is_staff:
        messages.error(request, _("No tienes permiso para enviar esta solicitud"))
        return redirect("materials_request_detail", request_id=request_id)

    if mat_request.submit_for_approval(request.user):
        messages.success(request, _("Solicitud enviada para aprobación"))
    else:
        messages.warning(request, _("La solicitud no está en estado borrador"))

    return redirect("materials_request_detail", request_id=request_id)


@login_required
@staff_required
@require_POST
def materials_request_approve(request, request_id):
    """Q14.4: Aprobar solicitud (solo admin)"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    if mat_request.approve(request.user):
        messages.success(request, _("Solicitud #%(id)s aprobada") % {"id": mat_request.id})
    else:
        messages.warning(request, _("La solicitud no está pendiente de aprobación"))

    return redirect("materials_request_detail", request_id=request_id)


@login_required
@staff_required
@require_POST
def materials_request_reject(request, request_id):
    """Q14.4: Rechazar solicitud"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    reason = request.POST.get("reason", "")

    mat_request.status = "cancelled"
    if reason:
        mat_request.notes = (mat_request.notes or "") + f"\n[Rechazada]: {reason}"
    mat_request.save()

    messages.success(request, _("Solicitud #%(id)s rechazada") % {"id": mat_request.id})
    return redirect("materials_requests_list_all")


@login_required
@staff_required
def materials_receive_partial(request, request_id):
    """Q14.10: Registrar recepción parcial de materiales"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    if request.method == "POST":
        received_data = {}

        for item in mat_request.items.all():
            qty_key = f"received_{item.id}"
            qty_value = request.POST.get(qty_key)

            if qty_value:
                try:
                    qty = Decimal(qty_value)
                    if qty > 0:
                        received_data[item.id] = qty
                except (ValueError, InvalidOperation):
                    continue

        if received_data:
            success, message = mat_request.receive_materials(received_data, request.user)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
        else:
            messages.warning(request, _("No se especificaron cantidades recibidas"))

        return redirect("materials_request_detail", request_id=request_id)

    # GET request - show form
    items = mat_request.items.all()
    return render(
        request,
        "core/materials_receive_partial.html",
        {
            "mat_request": mat_request,
            "items": items,
        },
    )


@login_required
@staff_required
@require_POST
def materials_create_expense(request, request_id):
    """Q14.6: Crear gasto automáticamente desde compra directa"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    total_amount_str = request.POST.get("total_amount")
    if not total_amount_str:
        messages.error(request, _("Debes especificar el monto total"))
        return redirect("materials_request_detail", request_id=request_id)

    try:
        total_amount = Decimal(total_amount_str)
        expense = mat_request.create_direct_purchase_expense(total_amount, request.user)
        messages.success(
            request,
            _("Gasto #%(id)s creado por $%(amount)s") % {"id": expense.id, "amount": total_amount},
        )
    except (ValueError, InvalidOperation):
        messages.error(request, _("Monto inválido"))
    except Exception as e:
        messages.error(request, _("Error al crear gasto: %(error)s") % {"error": str(e)})

    return redirect("materials_request_detail", request_id=request_id)


@login_required
def inventory_low_stock_alert(request):
    """Q15.5: Dashboard de alertas de stock bajo"""
    from core.models import ProjectInventory

    # Get all inventory items below threshold
    low_stock_items = []

    for stock in ProjectInventory.objects.select_related("item", "location", "location__project"):
        if stock.is_below:
            low_stock_items.append(
                {
                    "stock": stock,
                    "threshold": stock.threshold(),
                    "deficit": stock.threshold() - stock.quantity if stock.threshold() else 0,
                }
            )

    # Sort by severity (highest deficit first)
    low_stock_items.sort(key=lambda x: x["deficit"], reverse=True)

    return render(
        request,
        "core/inventory_low_stock.html",
        {
            "low_stock_items": low_stock_items,
        },
    )


@login_required
@staff_required
@require_POST
def inventory_adjust(request, item_id, location_id):
    """Q15.11: Ajuste manual de inventario con audit trail"""
    from core.models import InventoryItem, InventoryLocation, InventoryMovement

    item = get_object_or_404(InventoryItem, pk=item_id)
    location = get_object_or_404(InventoryLocation, pk=location_id)

    quantity_str = request.POST.get("quantity")
    reason = request.POST.get("reason", "")

    if not quantity_str or not reason:
        messages.error(request, _("Cantidad y razón son requeridos"))
        return redirect("inventory_view", project_id=location.project_id)

    try:
        quantity = Decimal(quantity_str)

        movement = InventoryMovement.objects.create(
            item=item,
            to_location=location,
            movement_type="ADJUST",
            quantity=quantity,
            reason=reason,  # Q15.11: Audit trail
            created_by=request.user,
        )
        movement.apply()

        messages.success(
            request,
            _("Inventario ajustado: %(quantity)s %(unit)s")
            % {"quantity": quantity, "unit": item.unit},
        )
    except (ValueError, InvalidOperation) as e:
        messages.error(request, _("Cantidad inválida: %(error)s") % {"error": str(e)})
    except Exception as e:
        messages.error(request, _("Error: %(error)s") % {"error": str(e)})

    return redirect("inventory_view", project_id=location.project_id)


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def inventory_wizard(request, project_id):
    """
    Modern wizard interface for inventory management
    Handles: Add (RECEIVE), Move (TRANSFER), Adjust (ADJUST)
    """
    from decimal import Decimal
    import json

    from django.core.exceptions import ValidationError
    from django.db.models import Q

    from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

    project = get_object_or_404(Project, pk=project_id)

    # Get all inventory items and locations
    items = InventoryItem.objects.all().order_by("category", "name")
    locations = InventoryLocation.objects.filter(Q(is_storage=True) | Q(project=project)).order_by(
        "is_storage", "name"
    )

    # Get all stock data for JavaScript
    stocks = ProjectInventory.objects.filter(location__in=locations).select_related(
        "item", "location"
    )

    stock_data = {}
    for stock in stocks:
        key = f"{stock.item.id}-{stock.location.id}"
        stock_data[key] = {
            "quantity": float(stock.quantity),
            "unit": stock.item.unit,
            "threshold": float(stock.threshold()) if stock.threshold() else None,
        }

    # Get low stock items
    low_stock_items = []
    for stock in stocks:
        if stock.is_below:
            low_stock_items.append(stock)

    # Handle POST request (form submission)
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            item_id = request.POST.get("item_id")
            quantity = Decimal(request.POST.get("quantity", "0"))
            reason = request.POST.get("reason", "")

            # Validate: for ADJUST, allow negative quantities; for others, require positive
            if not item_id or not reason:
                raise ValidationError(_("Please fill all required fields"))

            if action != "adjust" and quantity <= 0:
                raise ValidationError(_("Quantity must be positive"))

            if action == "adjust" and quantity == 0:
                raise ValidationError(_("Adjustment quantity cannot be zero"))

            item = get_object_or_404(InventoryItem, pk=item_id)

            if action == "add":
                # RECEIVE movement
                to_location_id = request.POST.get("to_location_id")
                unit_price = request.POST.get("unit_price")

                to_location = get_object_or_404(InventoryLocation, pk=to_location_id)

                movement = InventoryMovement.objects.create(
                    item=item,
                    to_location=to_location,
                    movement_type="RECEIVE",
                    quantity=quantity,
                    unit_cost=Decimal(unit_price)
                    if unit_price
                    else None,  # Changed from unit_price to unit_cost
                    reason=reason,
                    created_by=request.user,
                )
                movement.apply()

                messages.success(
                    request,
                    _("Successfully added %(quantity)s %(unit)s of %(item)s to %(location)s")
                    % {
                        "quantity": quantity,
                        "unit": item.unit,
                        "item": item.name,
                        "location": to_location.name,
                    },
                )

            elif action == "move":
                # TRANSFER movement
                from_location_id = request.POST.get("from_location_id")
                to_location_id = request.POST.get("to_location_id")

                if from_location_id == to_location_id:
                    raise ValidationError(_("Source and destination locations must be different"))

                from_location = get_object_or_404(InventoryLocation, pk=from_location_id)
                to_location = get_object_or_404(InventoryLocation, pk=to_location_id)

                movement = InventoryMovement.objects.create(
                    item=item,
                    from_location=from_location,
                    to_location=to_location,
                    movement_type="TRANSFER",
                    quantity=quantity,
                    reason=reason,
                    created_by=request.user,
                )
                movement.apply()

                messages.success(
                    request,
                    _(
                        "Successfully moved %(quantity)s %(unit)s of %(item)s from %(from)s to %(to)s"
                    )
                    % {
                        "quantity": quantity,
                        "unit": item.unit,
                        "item": item.name,
                        "from": from_location.name,
                        "to": to_location.name,
                    },
                )

            elif action == "adjust":
                # ADJUST movement
                to_location_id = request.POST.get("to_location_id")
                to_location = get_object_or_404(InventoryLocation, pk=to_location_id)

                movement = InventoryMovement.objects.create(
                    item=item,
                    to_location=to_location,
                    movement_type="ADJUST",
                    quantity=quantity,  # Can be negative
                    reason=reason,
                    created_by=request.user,
                )
                movement.apply()

                action_text = _("increased") if quantity > 0 else _("decreased")
                messages.success(
                    request,
                    _(
                        "Successfully %(action)s stock of %(item)s by %(quantity)s %(unit)s at %(location)s"
                    )
                    % {
                        "action": action_text,
                        "item": item.name,
                        "quantity": abs(quantity),
                        "unit": item.unit,
                        "location": to_location.name,
                    },
                )

            else:
                raise ValidationError(_("Invalid action"))

            # Redirect back to wizard
            return redirect("inventory_wizard", project_id=project.id)

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, _("Error: %(error)s") % {"error": str(e)})

    # Render wizard template
    return render(
        request,
        "core/inventory_wizard.html",
        {
            "project": project,
            "items": items,
            "locations": locations,
            "stock_data_json": json.dumps(stock_data),
            "low_stock_items": low_stock_items,
            "low_stock_count": len(low_stock_items),
        },
    )


# ===========================
# DAILY PLANNING SYSTEM VIEWS
# ===========================


