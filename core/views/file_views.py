"""File organization & workflow views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _is_staffish,
    _require_admin_or_redirect,
    logger,
    pisa,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


# ========================================================================================
# FILE ORGANIZATION VIEWS
# ========================================================================================


@login_required
def project_files_view(request, project_id):
    """Main view for project file organization system - Odoo-style workspace"""
    from core.forms import FileCategoryForm, ProjectFileForm
    from core.models import DocumentTag, FileCategory, ProjectFile

    project = get_object_or_404(Project, id=project_id)

    # Get or create default categories
    default_categories = [
        ("Daily Logs Photos", "daily_logs", "bi-camera-fill", "primary"),
        ("Documents", "documents", "bi-file-earmark-text", "info"),
        ("Datasheets", "datasheets", "bi-file-spreadsheet", "success"),
        ("Signed Change Orders", "cos_signed", "bi-file-earmark-check", "warning"),
        ("Signed Color Samples", "colorsamples_signed", "bi-palette", "purple"),
        ("Invoices", "invoices", "bi-receipt", "success"),
        ("Contracts", "contracts", "bi-file-earmark-ruled", "danger"),
        ("Photos", "photos", "bi-images", "primary"),
    ]

    for idx, (name, cat_type, icon, color) in enumerate(default_categories):
        FileCategory.objects.get_or_create(
            project=project,
            name=name,
            parent=None,
            defaults={
                "category_type": cat_type,
                "icon": icon,
                "color": color,
                "order": idx,
                "created_by": request.user,
            },
        )

    # Get root categories (no parent)
    categories = project.file_categories.filter(parent=None).prefetch_related("children")
    
    # Get selected category
    selected_category_id = request.GET.get("category")
    selected_category = None
    if selected_category_id:
        selected_category = FileCategory.objects.filter(id=selected_category_id, project=project).first()

    # Build file queryset
    files = ProjectFile.objects.filter(project=project).select_related(
        "category", "uploaded_by"
    ).prefetch_related("document_tags")

    # Filter by category
    if selected_category_id:
        files = files.filter(category_id=selected_category_id)

    # Filter by favorites
    if request.GET.get("favorites"):
        files = files.filter(is_favorited=True)

    # Filter by tag
    tag_filter = request.GET.get("tag")
    if tag_filter:
        files = files.filter(document_tags__id=tag_filter)

    # Search filter
    search_query = request.GET.get("q")
    if search_query:
        files = files.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    # Filter by public files (shared with client)
    if request.GET.get("public"):
        files = files.filter(is_public=True)

    # Get all tags for the project
    all_tags = DocumentTag.objects.filter(project=project)
    
    # Stats
    total_files = ProjectFile.objects.filter(project=project).count()
    favorites_count = ProjectFile.objects.filter(project=project, is_favorited=True).count()
    public_count = ProjectFile.objects.filter(project=project, is_public=True).count()

    return render(
        request,
        "core/documents_workspace.html",
        {
            "project": project,
            "categories": categories,
            "files": files,
            "selected_category": selected_category,
            "selected_category_id": selected_category_id,
            "search_query": search_query or "",
            "all_tags": all_tags,
            "total_files": total_files,
            "favorites_count": favorites_count,
            "public_count": public_count,
            "category_form": FileCategoryForm(),
            "file_form": ProjectFileForm(),
        },
    )


@login_required
def file_category_create(request, project_id):
    """Create a new file category - Staff only"""
    from core.forms import FileCategoryForm

    # Security: Only staff can create categories
    if not request.user.is_staff:
        messages.error(request, _("You don't have permission to create folders"))
        return redirect("client_documents", project_id=project_id)

    if request.method != "POST":
        return redirect("project_files", project_id=project_id)

    project = get_object_or_404(Project, id=project_id)
    form = FileCategoryForm(request.POST)

    if form.is_valid():
        category = form.save(commit=False)
        category.project = project
        category.created_by = request.user
        category.save()
        messages.success(request, f'Categoría "{category.name}" creada')
    else:
        messages.error(request, "Error al crear categoría")

    return redirect("project_files", project_id=project_id)


@login_required
@require_POST
def file_upload(request, project_id, category_id):
    """Upload a file to a category - Staff only"""
    from core.forms import ProjectFileForm
    from core.models import FileCategory

    # Security: Only staff can upload files
    if not request.user.is_staff:
        return JsonResponse({"error": gettext("No tienes permiso para subir archivos")}, status=403)

    project = get_object_or_404(Project, id=project_id)
    
    # Si category_id es 0, usar la categoría "Documents" por defecto
    if category_id == 0:
        category = FileCategory.objects.filter(
            project=project, 
            category_type="documents"
        ).first()
        if not category:
            # Crear categoría Documents si no existe
            category = FileCategory.objects.create(
                project=project,
                name="Documents",
                category_type="documents",
                icon="bi-file-earmark-text",
                color="info",
                created_by=request.user,
            )
    else:
        category = get_object_or_404(FileCategory, id=category_id, project=project)

    form = ProjectFileForm(request.POST, request.FILES)
    if form.is_valid():
        file_obj = form.save(commit=False)
        file_obj.project = project
        file_obj.category = category
        file_obj.uploaded_by = request.user
        
        # Si el nombre está vacío, usar el nombre del archivo
        if not file_obj.name and request.FILES.get('file'):
            file_obj.name = request.FILES['file'].name
        
        file_obj.save()
        messages.success(request, f'Archivo "{file_obj.name}" subido correctamente')
    else:
        messages.error(request, "Error al subir archivo")

    return redirect("project_files", project_id=project_id)


@login_required
@require_POST
def file_delete(request, file_id):
    """Delete a file"""
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    project_id = file_obj.project.id

    # Check permission
    if not (request.user.is_staff or request.user == file_obj.uploaded_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Delete file from storage
    if file_obj.file:
        file_obj.file.delete()

    file_name = file_obj.name
    file_obj.delete()

    messages.success(request, f'Archivo "{file_name}" eliminado')
    return redirect("project_files", project_id=project_id)


@login_required
def file_download(request, file_id):
    """Download a file"""
    from core.models import ProjectFile
    from django.http import FileResponse
    import mimetypes

    file_obj = get_object_or_404(ProjectFile, id=file_id)

    # Check permissions - client can only download public files from their projects
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "client":
        if not file_obj.is_public:
            return HttpResponseForbidden("No tienes permiso para descargar este archivo")
        # Also verify client has access to this project
        from core.models import ClientProjectAccess
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=file_obj.project
        ).exists()
        is_project_client = False
        if file_obj.project.client:
            _ct = file_obj.project.client.strip().lower()
            is_project_client = _ct in (
                request.user.email.lower(),
                request.user.get_full_name().lower(),
                request.user.username.lower(),
            )
        if not (has_access or is_project_client):
            return HttpResponseForbidden("No tienes acceso a este proyecto")

    # Serve file
    if file_obj.file:
        try:
            # Increment download counter
            file_obj.download_count = (file_obj.download_count or 0) + 1
            file_obj.save(update_fields=['download_count'])
            
            # Get content type
            content_type, _ = mimetypes.guess_type(file_obj.name)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Use FileResponse for better handling (works with S3 and local)
            response = FileResponse(
                file_obj.file.open('rb'),
                content_type=content_type,
                as_attachment=True,
                filename=file_obj.name
            )
            return response
        except FileNotFoundError:
            # File doesn't exist on disk - try to regenerate if it's a signed document
            logger.warning(f"File not found on disk: {file_obj.name}, attempting regeneration...")
            
            # Try to regenerate CO or ColorSample PDFs
            if file_obj.name.startswith("CO_") or file_obj.name.startswith("ChangeOrder_"):
                try:
                    from core.models import ChangeOrder
                    from core.services.pdf_service import generate_signed_changeorder_pdf
                    from django.core.files.base import ContentFile
                    
                    # Extract CO ID from filename (CO_13_xxx or ChangeOrder_13_xxx)
                    parts = file_obj.name.split("_")
                    co_id = int(parts[1])
                    co = ChangeOrder.objects.get(id=co_id)
                    
                    if co.signed_at:
                        pdf_bytes = generate_signed_changeorder_pdf(co)
                        # Save regenerated file
                        file_obj.file.save(file_obj.name, ContentFile(pdf_bytes), save=True)
                        logger.info(f"Regenerated CO PDF: {file_obj.name}")
                        
                        response = HttpResponse(pdf_bytes, content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
                        return response
                except Exception as regen_error:
                    logger.error(f"Failed to regenerate CO PDF: {regen_error}")
            
            elif file_obj.name.startswith("ColorSample_"):
                try:
                    from core.models import ColorSample
                    from core.services.pdf_service import generate_signed_colorsample_pdf
                    from django.core.files.base import ContentFile
                    
                    # Extract sample ID from filename (ColorSample_XX_code_project.pdf)
                    parts = file_obj.name.split("_")
                    sample_id = parts[1]
                    # Could be ID or sample_number
                    cs = ColorSample.objects.filter(
                        models.Q(id=sample_id) | models.Q(sample_number=sample_id),
                        project=file_obj.project
                    ).first()
                    
                    if cs and cs.client_signed_at:
                        pdf_bytes = generate_signed_colorsample_pdf(cs)
                        # Save regenerated file
                        file_obj.file.save(file_obj.name, ContentFile(pdf_bytes), save=True)
                        logger.info(f"Regenerated ColorSample PDF: {file_obj.name}")
                        
                        response = HttpResponse(pdf_bytes, content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{file_obj.name}"'
                        return response
                except Exception as regen_error:
                    logger.error(f"Failed to regenerate ColorSample PDF: {regen_error}")
            
            return HttpResponseNotFound("El archivo no está disponible. Por favor contacte al administrador.")
        except Exception as e:
            logger.error(f"File download error: {e}")
            return HttpResponseNotFound("Error al descargar. Por favor contacte al administrador.")

    return HttpResponseNotFound("Archivo no encontrado")


@login_required
def file_edit_metadata(request, file_id):
    """Edit file metadata (name, description, tags, version)"""
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)

    # Check permission
    if not (request.user.is_staff or request.user == file_obj.uploaded_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        file_obj.name = request.POST.get("name", file_obj.name)
        file_obj.description = request.POST.get("description", "")
        file_obj.tags = request.POST.get("tags", "")
        file_obj.version = request.POST.get("version", "")
        file_obj.save()

        messages.success(request, f'Archivo "{file_obj.name}" actualizado')

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": gettext("Archivo actualizado")})

        return redirect("project_files", project_id=file_obj.project.id)

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def file_details_api(request, file_id):
    """API endpoint to get file details for the panel"""
    from core.models import ProjectFile, ClientProjectAccess

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    # === ACCESS CONTROL ===
    profile = getattr(request.user, "profile", None)
    is_client = profile and profile.role == "client"
    
    if is_client:
        # Client can only see public files from their projects
        if not file_obj.is_public:
            return JsonResponse({"error": "No tienes permiso"}, status=403)
        
        # Verify client has access to this project
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=file_obj.project
        ).exists()
        is_project_client = False
        if file_obj.project.client:
            _ct = file_obj.project.client.strip().lower()
            is_project_client = _ct in (
                request.user.email.lower(),
                request.user.get_full_name().lower(),
                request.user.username.lower(),
            )
        if not (has_access or is_project_client):
            return JsonResponse({"error": "No tienes acceso a este proyecto"}, status=403)
    
    # Icon color mapping
    icon_colors = {
        "pdf": "#ef4444",
        "image": "#8b5cf6",
        "spreadsheet": "#10b981",
        "word": "#3b82f6",
        "cad": "#f59e0b",
        "video": "#ec4899",
        "other": "#6b7280",
    }
    
    # Build response - limit info for clients
    # Check if file can be regenerated (for estimate/contract PDFs)
    can_regenerate = False
    document_type = getattr(file_obj, 'document_type', '') or ''
    if not is_client:
        if document_type in ['contract', 'estimate']:
            can_regenerate = True
        elif file_obj.name and ('Contract_' in file_obj.name or 'Estimate_' in file_obj.name):
            # Also detect by filename pattern for older files without document_type
            can_regenerate = True
    
    data = {
        "id": file_obj.id,
        "name": file_obj.name,
        "description": file_obj.description or "",
        "file_type": file_obj.get_file_type_display(),
        "file_url": file_obj.file.url if file_obj.file else "",
        "icon": file_obj.get_icon(),
        "icon_color": icon_colors.get(file_obj.file_type, "#6b7280"),
        "size": file_obj.get_size_display(),
        "uploaded_at": file_obj.uploaded_at.strftime("%d/%m/%Y %H:%M"),
        "uploaded_by": file_obj.uploaded_by.username if file_obj.uploaded_by else "Sistema",
        "version": file_obj.version or "",
        "is_favorited": file_obj.is_favorited,
        "download_count": file_obj.download_count,
        "is_client_view": is_client,  # Flag to hide edit features in frontend
        "document_type": document_type,  # For regenerate PDF button
        "can_regenerate_pdf": can_regenerate,
        "tags": [
            {"id": t.id, "name": t.name, "color": t.color}
            for t in file_obj.document_tags.all()
        ],
    }
    
    return JsonResponse(data)


@login_required
@require_POST
def file_regenerate_pdf(request, file_id):
    """Regenerate PDF for Contract/Estimate documents - STAFF ONLY"""
    from core.models import ProjectFile, Estimate
    
    if not request.user.is_staff:
        return JsonResponse({"error": gettext("Solo staff puede regenerar PDFs")}, status=403)
    
    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    # Check if this is a contract/estimate PDF (by document_type or filename pattern)
    document_type = getattr(file_obj, 'document_type', '') or ''
    is_regenerable = document_type in ['contract', 'estimate']
    if not is_regenerable and file_obj.name:
        is_regenerable = 'Contract_' in file_obj.name or 'Estimate_' in file_obj.name
    
    if not is_regenerable:
        return JsonResponse({"error": gettext("Este archivo no es un contrato/estimado regenerable")}, status=400)
    
    # Try to find the source estimate
    estimate = None
    source_content_type = getattr(file_obj, 'source_content_type', None)
    source_object_id = getattr(file_obj, 'source_object_id', None)
    if source_content_type and source_object_id:
        from django.contrib.contenttypes.models import ContentType
        ct = source_content_type
        if ct.model == 'estimate':
            estimate = Estimate.objects.filter(id=source_object_id).first()
    
    # If not linked, try to find by filename pattern
    if not estimate and file_obj.name:
        import re
        # Pattern: Contract_KPIS1000_PRJ-2026-002.pdf or Estimate_KPIS1000_PRJ-2026-002.pdf
        match = re.search(r'(Contract|Estimate)_([A-Z0-9]+)_', file_obj.name)
        if match:
            code = match.group(2)
            estimate = Estimate.objects.filter(
                code__icontains=code,
                project=file_obj.project
            ).first()
    
    if not estimate:
        return JsonResponse({"error": gettext("No se encontró el estimado asociado a este archivo")}, status=404)
    
    try:
        if estimate.approved:
            # Use new Contract system for approved estimates
            from core.services.contract_service import ContractService
            
            # Get or create contract
            if hasattr(estimate, 'contract') and estimate.contract:
                contract = estimate.contract
            else:
                # Create contract if doesn't exist (for legacy approved estimates)
                contract = ContractService.create_contract_from_estimate(
                    estimate=estimate,
                    user=request.user,
                    auto_generate_pdf=False
                )
            
            # Regenerate PDF with new professional format
            result = ContractService.generate_contract_pdf(contract, request.user)
            if result:
                logger.info(f"Contract PDF regenerated for estimate {estimate.code} by {request.user.username}")
                return JsonResponse({
                    "success": True,
                    "message": gettext("Contract PDF regenerated with professional format"),
                    "file_id": result.id,
                })
            else:
                return JsonResponse({"error": gettext("Error al regenerar PDF del contrato")}, status=500)
        else:
            # For non-approved estimates, use regular estimate PDF
            from core.services.document_storage_service import auto_save_estimate_pdf
            result = auto_save_estimate_pdf(
                estimate, 
                user=request.user, 
                as_contract=False,
                overwrite=True
            )
            if result:
                logger.info(f"Estimate PDF regenerated for {estimate.code} by {request.user.username}")
                return JsonResponse({
                    "success": True,
                    "message": gettext("Estimate PDF regenerated"),
                    "file_id": result.id,
                })
            else:
                return JsonResponse({"error": gettext("Error al regenerar PDF")}, status=500)
    except Exception as e:
        logger.error(f"Failed to regenerate PDF: {e}")
        return JsonResponse({"error": gettext("Error al regenerar PDF")}, status=500)


@login_required
@require_POST
def file_toggle_favorite(request, file_id):
    """Toggle file favorite status"""
    from core.models import ProjectFile, ClientProjectAccess

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    # === ACCESS CONTROL ===
    profile = getattr(request.user, "profile", None)
    is_client = profile and profile.role == "client"
    
    if is_client:
        # Client can only favorite public files from their projects
        if not file_obj.is_public:
            return JsonResponse({"error": "No tienes permiso"}, status=403)
        
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=file_obj.project
        ).exists()
        is_project_client = False
        if file_obj.project.client:
            _ct = file_obj.project.client.strip().lower()
            is_project_client = _ct in (
                request.user.email.lower(),
                request.user.get_full_name().lower(),
                request.user.username.lower(),
            )
        if not (has_access or is_project_client):
            return JsonResponse({"error": "No tienes acceso"}, status=403)
    
    file_obj.is_favorited = not file_obj.is_favorited
    file_obj.save(update_fields=["is_favorited"])
    
    return JsonResponse({
        "success": True,
        "favorited": file_obj.is_favorited,
    })


@login_required
@require_POST
def file_toggle_public(request, file_id):
    """Toggle file public status (visible to client) - STAFF ONLY"""
    from core.models import ProjectFile

    # Only staff can change public status
    if not request.user.is_staff:
        return JsonResponse({"error": "Solo staff puede cambiar estado público"}, status=403)

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    file_obj.is_public = not file_obj.is_public
    file_obj.save(update_fields=["is_public"])
    
    # Count public files for the project
    public_count = ProjectFile.objects.filter(
        project=file_obj.project,
        is_public=True
    ).count()
    
    return JsonResponse({
        "success": True,
        "is_public": file_obj.is_public,
        "public_count": public_count,
    })


# ========================================================================================
# FILE SHARING SYSTEM (Odoo-style)
# ========================================================================================

@login_required
@require_POST
def file_generate_share_link(request, file_id):
    """Generate a shareable link for a file"""
    import secrets
    from datetime import timedelta
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    # Check permission
    if not (request.user.is_staff or request.user == file_obj.uploaded_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)
    
    # Get expiration days from request (default 7)
    try:
        expires_days = int(request.POST.get("expires_days", 7))
        if expires_days < 1:
            expires_days = 1
        elif expires_days > 365:
            expires_days = 365
    except (ValueError, TypeError):
        expires_days = 7
    
    # Generate token
    file_obj.share_token = secrets.token_urlsafe(32)
    file_obj.share_expires = timezone.now() + timedelta(days=expires_days)
    file_obj.is_shared = True
    file_obj.save(update_fields=["share_token", "share_expires", "is_shared"])
    
    # Build share URL
    share_url = request.build_absolute_uri(
        reverse("file_public_view", kwargs={"token": file_obj.share_token})
    )
    
    return JsonResponse({
        "success": True,
        "share_url": share_url,
        "token": file_obj.share_token,
        "expires": file_obj.share_expires.strftime("%d/%m/%Y %H:%M"),
        "expires_days": expires_days,
    })


@login_required
@require_POST
def file_revoke_share_link(request, file_id):
    """Revoke a file's share link"""
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    # Check permission
    if not (request.user.is_staff or request.user == file_obj.uploaded_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)
    
    file_obj.share_token = ""
    file_obj.share_expires = None
    file_obj.is_shared = False
    file_obj.save(update_fields=["share_token", "share_expires", "is_shared"])
    
    return JsonResponse({
        "success": True,
        "message": gettext("Link de compartir revocado"),
    })


def file_public_view(request, token):
    """Public view for shared files - no login required"""
    from core.models import ProjectFile

    # Find file by token
    file_obj = get_object_or_404(ProjectFile, share_token=token, is_shared=True)
    
    # Check if link has expired
    if file_obj.share_expires and file_obj.share_expires < timezone.now():
        return render(request, "core/file_share_expired.html", {
            "message": gettext("Este link ha expirado"),
        })
    
    # Icon color mapping
    icon_colors = {
        "pdf": "#ef4444",
        "image": "#8b5cf6",
        "spreadsheet": "#10b981",
        "word": "#3b82f6",
        "cad": "#f59e0b",
        "video": "#ec4899",
        "other": "#6b7280",
    }
    
    return render(request, "core/file_public_view.html", {
        "file": file_obj,
        "project": file_obj.project,
        "icon_color": icon_colors.get(file_obj.file_type, "#6b7280"),
    })


def file_public_download(request, token):
    """Download a shared file - no login required"""
    from core.models import ProjectFile

    # Find file by token
    file_obj = get_object_or_404(ProjectFile, share_token=token, is_shared=True)
    
    # Check if link has expired
    if file_obj.share_expires and file_obj.share_expires < timezone.now():
        return HttpResponseForbidden(gettext("Este link ha expirado"))
    
    # Increment download count
    file_obj.download_count += 1
    file_obj.save(update_fields=["download_count"])
    
    # Serve file
    if file_obj.file:
        response = HttpResponse(file_obj.file, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{file_obj.name}"'
        return response
    
    return HttpResponseNotFound(gettext("Archivo no encontrado"))


@login_required
@require_POST
def folder_generate_share_link(request, category_id):
    """Generate a shareable link for a folder/workspace"""
    import secrets
    from datetime import timedelta
    from core.models import FileCategory

    folder = get_object_or_404(FileCategory, id=category_id)
    
    # Check permission
    if not (request.user.is_staff or request.user == folder.created_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)
    
    # Get options from request
    try:
        expires_days = int(request.POST.get("expires_days", 7))
        if expires_days < 1:
            expires_days = 1
        elif expires_days > 365:
            expires_days = 365
    except (ValueError, TypeError):
        expires_days = 7
    
    allow_upload = request.POST.get("allow_upload") == "true"
    
    # Generate token
    folder.share_token = secrets.token_urlsafe(32)
    folder.is_shared = True
    folder.allow_upload = allow_upload
    folder.save(update_fields=["share_token", "is_shared", "allow_upload"])
    
    # Build share URL
    share_url = request.build_absolute_uri(
        reverse("folder_public_view", kwargs={"token": folder.share_token})
    )
    
    return JsonResponse({
        "success": True,
        "share_url": share_url,
        "token": folder.share_token,
        "allow_upload": allow_upload,
    })


def folder_public_view(request, token):
    """Public view for shared folders - no login required"""
    from core.models import FileCategory, ProjectFile

    # Find folder by token
    folder = get_object_or_404(FileCategory, share_token=token, is_shared=True)
    
    # Get files in this folder
    files = ProjectFile.objects.filter(category=folder).order_by("-uploaded_at")
    
    return render(request, "core/folder_public_view.html", {
        "folder": folder,
        "project": folder.project,
        "files": files,
        "allow_upload": folder.allow_upload,
    })


@require_POST
def folder_public_upload(request, token):
    """Upload files to a shared folder - no login required"""
    from core.models import FileCategory, ProjectFile

    # Find folder by token
    folder = get_object_or_404(FileCategory, share_token=token, is_shared=True)
    
    # Check if uploads are allowed
    if not folder.allow_upload:
        return JsonResponse({"error": gettext("Subidas no permitidas")}, status=403)
    
    # Handle file upload
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": gettext("No se recibió archivo")}, status=400)

    # SECURITY: Validate file size (max 25 MB)
    max_size = 25 * 1024 * 1024  # 25 MB
    if uploaded_file.size > max_size:
        return JsonResponse({"error": gettext("El archivo excede el tamaño máximo de 25 MB")}, status=400)

    # SECURITY: Validate file extension
    import os
    allowed_extensions = {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic",
        ".mp4", ".mov", ".avi", ".dwg", ".dxf", ".zip", ".rar",
    }
    _, ext = os.path.splitext(uploaded_file.name.lower())
    if ext not in allowed_extensions:
        return JsonResponse({"error": gettext("Tipo de archivo no permitido")}, status=400)
    
    # Create file record
    file_obj = ProjectFile.objects.create(
        project=folder.project,
        category=folder,
        file=uploaded_file,
        name=uploaded_file.name,
        uploaded_by=None,  # Anonymous upload
    )
    
    return JsonResponse({
        "success": True,
        "file_id": file_obj.id,
        "file_name": file_obj.name,
        "message": gettext("Archivo subido correctamente"),
    })


# ========================================================================================
# DOCUMENT WORKFLOW API (Odoo-style Phase 3)
# ========================================================================================


@login_required
def workflow_templates_list(request, project_id):
    """List all workflow templates for a project"""
    from core.models import DocumentWorkflowTemplate

    project = get_object_or_404(Project, id=project_id)
    templates = DocumentWorkflowTemplate.objects.filter(project=project, is_active=True)
    
    data = [{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "steps_count": t.steps.count(),
        "auto_category": t.auto_assign_to_category.name if t.auto_assign_to_category else None,
    } for t in templates]
    
    return JsonResponse({"templates": data})


@login_required
@require_POST
def workflow_template_create(request, project_id):
    """Create a new workflow template"""
    from core.models import DocumentWorkflowTemplate, WorkflowStep
    import json

    project = get_object_or_404(Project, id=project_id)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    template = DocumentWorkflowTemplate.objects.create(
        project=project,
        name=data.get("name", "Nuevo Workflow"),
        description=data.get("description", ""),
        created_by=request.user,
    )
    
    # Create steps
    for i, step_data in enumerate(data.get("steps", [])):
        WorkflowStep.objects.create(
            workflow=template,
            name=step_data.get("name", f"Paso {i+1}"),
            step_type=step_data.get("type", "approve"),
            order=i,
            assigned_role=step_data.get("role", ""),
            requires_comment=step_data.get("requires_comment", False),
            requires_signature=step_data.get("requires_signature", False),
        )
    
    return JsonResponse({
        "success": True,
        "template_id": template.id,
        "message": gettext("Workflow creado correctamente"),
    })


@login_required
@require_POST
def workflow_start(request, file_id):
    """Start a workflow for a document - Staff only"""
    from core.models import ProjectFile, DocumentWorkflow, DocumentWorkflowTemplate
    import json

    # Only staff can start workflows
    if not request.user.is_staff:
        return JsonResponse({"error": gettext("No tienes permiso para iniciar workflows")}, status=403)

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    
    template_id = data.get("template_id")
    if not template_id:
        # Try to get default template for this category
        template = DocumentWorkflowTemplate.objects.filter(
            auto_assign_to_category=file_obj.category,
            is_active=True
        ).first()
    else:
        template = get_object_or_404(DocumentWorkflowTemplate, id=template_id)
    
    if not template:
        return JsonResponse({"error": gettext("No hay workflow disponible")}, status=400)
    
    # Check if there's already an active workflow
    existing = DocumentWorkflow.objects.filter(
        file=file_obj,
        status__in=["pending", "in_progress"]
    ).exists()
    
    if existing:
        return JsonResponse({"error": gettext("Ya existe un workflow activo")}, status=400)
    
    # Create workflow instance
    workflow = DocumentWorkflow.objects.create(
        file=file_obj,
        template=template,
        status="in_progress",
        current_step=0,
        initiated_by=request.user,
    )
    
    return JsonResponse({
        "success": True,
        "workflow_id": workflow.id,
        "message": gettext("Workflow iniciado"),
    })


@login_required
def workflow_detail(request, workflow_id):
    """Get workflow details and progress"""
    from core.models import DocumentWorkflow

    workflow = get_object_or_404(DocumentWorkflow, id=workflow_id)
    
    # Security: Non-staff can only see workflows for public files they have access to
    if not request.user.is_staff:
        file_obj = workflow.file
        if not file_obj.is_public:
            return JsonResponse({"error": gettext("No tienes acceso a este archivo")}, status=403)
        if not file_obj.project.clients.filter(id=request.user.id).exists():
            return JsonResponse({"error": gettext("No tienes acceso a este proyecto")}, status=403)
    
    # Get all steps with their actions
    steps_data = []
    if workflow.template:
        for step in workflow.template.steps.all():
            actions = workflow.step_actions.filter(step=step)
            steps_data.append({
                "id": step.id,
                "name": step.name,
                "type": step.step_type,
                "order": step.order,
                "is_current": step.order == workflow.current_step,
                "is_completed": actions.filter(action__in=["approved", "signed"]).exists(),
                "requires_signature": step.requires_signature,
                "requires_comment": step.requires_comment,
                "actions": [{
                    "action": a.action,
                    "performed_by": a.performed_by.get_full_name() if a.performed_by else "Sistema",
                    "performed_at": a.performed_at.isoformat(),
                    "comment": a.comment,
                } for a in actions]
            })
    
    return JsonResponse({
        "id": workflow.id,
        "file_name": workflow.file.name,
        "file_id": workflow.file.id,
        "status": workflow.status,
        "status_display": workflow.get_status_display(),
        "progress": workflow.get_progress_percentage(),
        "current_step": workflow.current_step,
        "initiated_by": workflow.initiated_by.get_full_name() if workflow.initiated_by else None,
        "initiated_at": workflow.initiated_at.isoformat(),
        "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
        "steps": steps_data,
    })


@login_required
@require_POST
def workflow_action(request, workflow_id):
    """Perform an action on the current workflow step"""
    from core.models import DocumentWorkflow, WorkflowStepAction
    import json

    workflow = get_object_or_404(DocumentWorkflow, id=workflow_id)
    
    # Security: Non-staff can only act on workflows for public files they have access to
    if not request.user.is_staff:
        file_obj = workflow.file
        if not file_obj.is_public:
            return JsonResponse({"error": gettext("No tienes acceso a este archivo")}, status=403)
        # Check they have access to the project
        if not file_obj.project.clients.filter(id=request.user.id).exists():
            return JsonResponse({"error": gettext("No tienes acceso a este proyecto")}, status=403)
    
    if workflow.status not in ["pending", "in_progress"]:
        return JsonResponse({"error": gettext("Workflow ya finalizado")}, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    
    action = data.get("action", "approved")
    comment = data.get("comment", "")
    
    current_step = workflow.get_current_step()
    if not current_step:
        return JsonResponse({"error": gettext("No hay paso actual")}, status=400)
    
    # Validate requirements
    if current_step.requires_comment and not comment:
        return JsonResponse({"error": gettext("Se requiere comentario")}, status=400)
    
    # Get client IP
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip_address = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
    
    # Create action record
    step_action = WorkflowStepAction.objects.create(
        workflow=workflow,
        step=current_step,
        action=action,
        performed_by=request.user,
        comment=comment,
        ip_address=ip_address,
    )
    
    # Handle signature if provided
    signature_data = data.get("signature")
    if signature_data and current_step.requires_signature:
        # Handle base64 signature image
        import base64
        from django.core.files.base import ContentFile
        
        if signature_data.startswith("data:image"):
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            step_action.signature_image.save(
                f"signature_{workflow_id}_{current_step.order}.{ext}",
                ContentFile(base64.b64decode(imgstr))
            )
    
    # Process action
    if action == "rejected":
        workflow.reject(request.user, comment)
        message = gettext("Documento rechazado")
    else:
        workflow.advance_to_next_step()
        if workflow.status == "approved":
            message = gettext("Workflow completado - Documento aprobado")
        else:
            message = gettext("Paso aprobado - Avanzando al siguiente")
    
    return JsonResponse({
        "success": True,
        "workflow_status": workflow.status,
        "progress": workflow.get_progress_percentage(),
        "message": message,
    })


@login_required
def file_workflow_status(request, file_id):
    """Get workflow status for a file"""
    from core.models import ProjectFile, DocumentWorkflow, ClientProjectAccess

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    
    # Security: Non-staff can only see workflows for public files they have access to
    if not request.user.is_staff:
        if not file_obj.is_public:
            return JsonResponse({"error": gettext("No tienes acceso a este archivo")}, status=403)
        # Check client access via ClientProjectAccess
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=file_obj.project
        ).exists()
        if not has_access:
            return JsonResponse({"error": gettext("No tienes acceso a este proyecto")}, status=403)
    
    # Get active or latest workflow
    workflow = DocumentWorkflow.objects.filter(file=file_obj).order_by("-initiated_at").first()
    
    if not workflow:
        return JsonResponse({
            "has_workflow": False,
            "can_start": request.user.is_staff,  # Only staff can start
        })
    
    return JsonResponse({
        "has_workflow": True,
        "workflow_id": workflow.id,
        "status": workflow.status,
        "status_display": workflow.get_status_display(),
        "progress": workflow.get_progress_percentage(),
        "can_start": request.user.is_staff and workflow.status in ["approved", "rejected", "cancelled"],
    })

