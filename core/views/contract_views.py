"""Contract & proposal views — edit, client view, public."""
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


# --- PUBLIC PROPOSAL APPROVAL ---
def proposal_public_view(request, token):
    """
    Public view for clients to approve or reject a proposal.
    No login required - access via unique token.
    """
    from core.models import Proposal

    try:
        proposal = Proposal.objects.select_related("estimate__project").get(client_view_token=token)
    except Proposal.DoesNotExist:
        return HttpResponseNotFound("Propuesta no encontrada o enlace inválido.")

    estimate = proposal.estimate
    project = estimate.project
    lines = estimate.lines.select_related("cost_code").all()

    # Calculate totals using the effective unit price (handles both direct price and breakdown)
    subtotal = sum(line.direct_cost() for line in lines)
    
    # Calculate material/labor totals for markup purposes
    total_material = sum(line.qty * line.material_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    total_labor = sum(line.qty * line.labor_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    
    # Apply markups and overheads
    markup_material_amount = total_material * (estimate.markup_material / Decimal("100"))
    markup_labor_amount = total_labor * (estimate.markup_labor / Decimal("100"))
    overhead_amount = subtotal * (estimate.overhead_pct / Decimal("100"))
    profit_amount = subtotal * (estimate.target_profit_pct / Decimal("100"))

    total = (
        subtotal + markup_material_amount + markup_labor_amount + overhead_amount + profit_amount
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            proposal.accepted = True
            proposal.accepted_at = timezone.now()
            estimate.approved = True
            proposal.save(update_fields=["accepted", "accepted_at"])
            estimate.save(update_fields=["approved"])
            
            # --- Auto-create Budget Lines from Estimate (with 30% profit margin) ---
            try:
                from core.services.budget_from_estimate import create_budget_from_estimate
                # Use target_profit_pct from estimate if set, otherwise default 30%
                profit_margin = estimate.target_profit_pct / Decimal("100") if estimate.target_profit_pct else None
                budget_lines = create_budget_from_estimate(estimate, profit_margin=profit_margin)
                logger.info(
                    f"Auto-created {len(budget_lines)} budget lines for approved Estimate {estimate.code}"
                )
            except Exception as e:
                logger.warning(f"Failed to auto-create budget from estimate: {e}")
            
            # --- Auto-create Contract from approved Estimate ---
            contract_url = None
            try:
                from core.services.contract_service import ContractService
                contract = ContractService.create_contract_from_estimate(
                    estimate=estimate,
                    user=None,
                    auto_generate_pdf=True
                )
                logger.info(
                    f"Auto-created contract {contract.contract_number} from approved Estimate {estimate.code}"
                )
                # Build contract signing URL
                from django.urls import reverse
                contract_url = reverse('contract_client_view', kwargs={'token': contract.client_view_token})
            except Exception as e:
                logger.warning(f"Failed to auto-create contract from estimate: {e}")
            
            # --- Auto-save Estimate/Contract PDF to Project Files (legacy, keep for backward compatibility) ---
            try:
                from core.tasks import auto_save_pdf_async

                est_id = estimate.id
                # Defer to Celery so client-facing approval response is fast.
                transaction.on_commit(
                    lambda: auto_save_pdf_async.delay(
                        doc_kind="estimate",
                        doc_id=est_id,
                        user_id=None,
                        as_contract=True,
                        overwrite=True,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to enqueue Estimate PDF auto-save: {e}")
            
            # Redirect to contract signing page if contract was created
            if contract_url:
                messages.success(
                    request,
                    _("Thank you! Your estimate has been approved. Please review and sign the contract to proceed.")
                )
                return redirect(contract_url)
            else:
                messages.success(
                    request,
                    _("Thank you! We have received your approval. We will begin working on your project.")
                )

        elif action == "reject":
            feedback = request.POST.get("feedback", "").strip()
            proposal.client_comment = feedback
            proposal.save(update_fields=["client_comment"])
            messages.info(
                request,
                _("We have received your comments. Our team will contact you soon.")
            )
            # Notify admins/PMs about proposal rejection
            staff_users = User.objects.filter(
                is_active=True,
                profile__role__in=["admin", "project_manager"],
            ).distinct()
            for u in staff_users:
                Notification.objects.create(
                    user=u,
                    project=project,
                    notification_type="change_order",
                    title=_("Proposal revision requested — %(project)s") % {"project": project.name},
                    message=_("Client feedback on proposal: %(feedback)s") % {
                        "feedback": (feedback[:200] + "...") if len(feedback) > 200 else feedback,
                    },
                    related_object_type="Proposal",
                    related_object_id=proposal.id,
                )

    context = {
        "proposal": proposal,
        "estimate": estimate,
        "project": project,
        "lines": lines,
        "subtotal": subtotal,
        "markup_material": markup_material_amount,
        "markup_labor": markup_labor_amount,
        "overhead": overhead_amount,
        "profit": profit_amount,
        "total": total,
    }

    return render(request, "core/proposal_public.html", context)



# --- STAFF CONTRACT EDIT VIEW ---
@login_required
def contract_edit_view(request, contract_id):
    """
    Staff view to edit contract details (dates, payment schedule, etc.)
    and regenerate PDF.
    """
    from core.models import Contract
    from core.services.contract_service import ContractService
    from datetime import datetime
    import json
    
    if not request.user.is_staff:
        messages.error(request, _("You don't have permission to edit contracts."))
        return redirect("home")
    
    contract = get_object_or_404(Contract, id=contract_id)
    estimate = contract.estimate
    project = contract.project
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "update_dates":
            # Update schedule dates
            start_date_str = request.POST.get("start_date")
            completion_date_str = request.POST.get("completion_date")
            
            try:
                if start_date_str:
                    contract.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                else:
                    contract.start_date = None
                    
                if completion_date_str:
                    contract.completion_date = datetime.strptime(completion_date_str, "%Y-%m-%d").date()
                else:
                    contract.completion_date = None
                
                contract.save(update_fields=["start_date", "completion_date", "updated_at"])
                messages.success(request, _("Contract dates updated successfully."))
            except ValueError as e:
                messages.error(request, _("Invalid date format."))
        
        elif action == "update_payment_schedule":
            # Update payment schedule from JSON
            try:
                payment_schedule_json = request.POST.get("payment_schedule", "[]")
                payment_schedule = json.loads(payment_schedule_json)
                
                # Recalculate amounts based on percentages
                total = float(contract.total_amount)
                for payment in payment_schedule:
                    payment["amount"] = str(round(total * payment["percentage"] / 100, 2))
                
                contract.payment_schedule = payment_schedule
                contract.save(update_fields=["payment_schedule", "updated_at"])
                messages.success(request, _("Payment schedule updated successfully."))
            except (json.JSONDecodeError, KeyError) as e:
                messages.error(request, _("Invalid payment schedule format."))
        
        elif action == "regenerate_pdf":
            # Regenerate PDF with current contract data
            try:
                result = ContractService.generate_contract_pdf(contract, request.user)
                if result:
                    messages.success(request, _("Contract PDF regenerated successfully."))
                else:
                    messages.error(request, _("Failed to regenerate PDF."))
            except Exception as e:
                messages.error(request, _(f"Error regenerating PDF: {str(e)}"))
        
        elif action == "send_to_client":
            # Mark as ready and get client link
            if contract.status == 'draft':
                contract.status = 'pending_signature'
                contract.save(update_fields=["status", "updated_at"])
            messages.success(request, _("Contract ready for client signature."))
        
        return redirect("contract_edit", contract_id=contract.id)
    
    # GET: Display edit form
    context = {
        "contract": contract,
        "estimate": estimate,
        "project": project,
        "lines": estimate.lines.select_related("cost_code").all(),
        "client_url": request.build_absolute_uri(f"/contracts/{contract.client_view_token}/"),
        "payment_schedule_json": json.dumps(contract.payment_schedule or []),
    }
    
    return render(request, "core/contract_edit.html", context)



# --- PUBLIC CONTRACT VIEW (FOR CLIENT SIGNATURE) ---
def contract_client_view(request, token):
    """
    Public view for clients to view and sign a contract.
    No login required - access via unique token.
    
    GET: Display contract details with signature form
    POST: Process signature or revision request
    """
    from core.models import Contract
    from core.services.contract_service import ContractService
    import base64
    
    # Get contract by token
    contract = ContractService.get_contract_by_token(token)
    
    if not contract:
        return HttpResponseNotFound("Contract not found or invalid link.")
    
    estimate = contract.estimate
    project = contract.project
    lines = estimate.lines.select_related("cost_code").all()
    
    # Calculate totals for display
    subtotal = sum(line.direct_cost() for line in lines)
    total_material = sum(line.qty * line.material_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    total_labor = sum(line.qty * line.labor_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    
    markup_material_amount = total_material * (estimate.markup_material / Decimal("100")) if estimate.markup_material else Decimal("0")
    markup_labor_amount = total_labor * (estimate.markup_labor / Decimal("100")) if estimate.markup_labor else Decimal("0")
    overhead_amount = subtotal * (estimate.overhead_pct / Decimal("100")) if estimate.overhead_pct else Decimal("0")
    profit_amount = subtotal * (estimate.target_profit_pct / Decimal("100")) if estimate.target_profit_pct else Decimal("0")
    
    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "sign" and contract.can_be_signed:
            # Get signature data
            client_name = request.POST.get("client_name", "").strip()
            signature_data_b64 = request.POST.get("signature_data", "")
            
            if not client_name:
                messages.error(request, _("Please enter your full name to sign the contract."))
            else:
                try:
                    # Decode signature if provided
                    signature_bytes = None
                    if signature_data_b64:
                        # Remove data URL prefix if present
                        if "," in signature_data_b64:
                            signature_data_b64 = signature_data_b64.split(",")[1]
                        signature_bytes = base64.b64decode(signature_data_b64)
                    
                    # Get client IP
                    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                    if x_forwarded_for:
                        client_ip = x_forwarded_for.split(",")[0].strip()
                    else:
                        client_ip = request.META.get("REMOTE_ADDR")
                    
                    # Sign the contract
                    contract = ContractService.sign_contract(
                        contract=contract,
                        client_name=client_name,
                        signature_data=signature_bytes,
                        ip_address=client_ip,
                        generate_signed_pdf=True,
                        user=None
                    )
                    
                    messages.success(
                        request,
                        _("Thank you! Your contract has been signed successfully. "
                          "You will receive a confirmation email shortly.")
                    )
                    
                    # Notify admins of signed contract
                    staff_users = User.objects.filter(
                        is_active=True,
                        profile__role__in=["admin", "project_manager"],
                    ).distinct()
                    for u in staff_users:
                        Notification.objects.create(
                            user=u,
                            project=contract.project,
                            notification_type="contract",
                            title=_("Contract signed — %(project)s") % {"project": contract.project.name},
                            message=_("%(client)s signed contract %(number)s for project %(project)s.") % {
                                "client": client_name,
                                "number": contract.contract_number,
                                "project": contract.project.name,
                            },
                            related_object_type="Contract",
                            related_object_id=contract.id,
                        )
                    
                except Exception as e:
                    logger.error(f"Error signing contract {contract.contract_number}: {e}")
                    messages.error(request, _("An error occurred while signing. Please try again."))
        
        elif action == "request_revision" and contract.status in ['pending_signature', 'revision_requested']:
            revision_notes = request.POST.get("revision_notes", "").strip()
            
            if not revision_notes:
                messages.error(request, _("Please provide details about the changes you need."))
            else:
                try:
                    contract = ContractService.request_revision(
                        contract=contract,
                        revision_notes=revision_notes
                    )
                    
                    messages.info(
                        request,
                        _("Your revision request has been submitted. "
                          "Our team will review and contact you soon.")
                    )
                    
                    # Notify admins of revision request
                    staff_users = User.objects.filter(
                        is_active=True,
                        profile__role__in=["admin", "project_manager"],
                    ).distinct()
                    for u in staff_users:
                        Notification.objects.create(
                            user=u,
                            project=contract.project,
                            notification_type="contract",
                            title=_("Contract revision requested — %(project)s") % {"project": contract.project.name},
                            message=_("Client requested revision on contract %(number)s: %(notes)s") % {
                                "number": contract.contract_number,
                                "notes": (revision_notes[:200] + "...") if len(revision_notes) > 200 else revision_notes,
                            },
                            related_object_type="Contract",
                            related_object_id=contract.id,
                        )
                    
                except Exception as e:
                    logger.error(f"Error requesting revision for {contract.contract_number}: {e}")
                    messages.error(request, _("An error occurred. Please try again."))
    
    # Build context
    context = {
        "contract": contract,
        "estimate": estimate,
        "project": project,
        "lines": lines,
        "subtotal": subtotal,
        "markup_material": markup_material_amount,
        "markup_labor": markup_labor_amount,
        "overhead": overhead_amount,
        "profit": profit_amount,
        "total": contract.total_amount,
        "payment_schedule": contract.payment_schedule or [],
        "is_signed": contract.is_signed,
        "can_be_signed": contract.can_be_signed,
        "status": contract.status,
    }
    
    return render(request, "core/contract_client_view.html", context)

