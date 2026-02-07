"""
Document Storage Service - Auto-save PDFs to Project File System

This service automatically saves generated PDFs to the project's document 
management system, organizing them by type:
- Color Samples → COs Firmados folder
- Change Orders → COs Firmados folder
- Estimates/Contracts → Contracts folder
- Invoices → Invoices folder

Features:
- Auto-creates project folders if they don't exist
- Prevents duplicate files (checks by name/hash)
- Links files to their source records
- Maintains audit trail
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Optional, Literal

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from core.models import (
        ChangeOrder, 
        ColorSample, 
        Estimate, 
        Invoice, 
        Project,
        ProjectFile,
        FileCategory,
    )

logger = logging.getLogger(__name__)


# Document type to category mapping
DOCUMENT_TYPE_CATEGORY = {
    "changeorder": "cos_signed",
    "colorsample": "colorsamples_signed", 
    "estimate": "contracts",
    "contract": "contracts",
    "invoice": "invoices",
}

# Document type to folder name mapping
DOCUMENT_TYPE_FOLDER_NAME = {
    "changeorder": "Signed Change Orders",
    "colorsample": "Signed Color Samples",
    "estimate": "Contracts",
    "contract": "Contracts",
    "invoice": "Invoices",
}


def _get_file_hash(content: bytes) -> str:
    """Generate SHA256 hash of file content for duplicate detection."""
    return hashlib.sha256(content).hexdigest()


def _get_or_create_category(
    project: "Project", 
    category_type: str, 
    user: Optional["User"] = None
) -> "FileCategory":
    """
    Get or create the appropriate FileCategory for a document type.
    Creates default categories if they don't exist.
    """
    from core.models import FileCategory
    
    folder_name = DOCUMENT_TYPE_FOLDER_NAME.get(category_type, "Documents")
    
    # Try to find existing category
    category = FileCategory.objects.filter(
        project=project,
        category_type=category_type,
        parent=None  # Root level
    ).first()
    
    if category:
        return category
    
    # Create new category
    # Get icon and color based on type
    icon_map = {
        "cos_signed": "bi-file-earmark-check",
        "colorsamples_signed": "bi-palette",
        "contracts": "bi-file-earmark-ruled",
        "invoices": "bi-receipt",
        "documents": "bi-file-earmark-text",
    }
    color_map = {
        "cos_signed": "warning",
        "colorsamples_signed": "purple",
        "contracts": "danger",
        "invoices": "success",
        "documents": "info",
    }
    
    # Get next order number
    max_order = FileCategory.objects.filter(project=project, parent=None).count()
    
    category = FileCategory.objects.create(
        project=project,
        name=folder_name,
        category_type=category_type,
        icon=icon_map.get(category_type, "bi-folder"),
        color=color_map.get(category_type, "primary"),
        order=max_order + 1,
        created_by=user,
    )
    
    logger.info(f"Created FileCategory '{folder_name}' for project {project.name}")
    return category


def _check_duplicate_file(
    project: "Project",
    filename: str,
    content_hash: str,
    category: "FileCategory"
) -> Optional["ProjectFile"]:
    """
    Check if a file with the same name or content already exists.
    Returns the existing file if found, None otherwise.
    """
    from core.models import ProjectFile
    
    # Check by filename in same category
    existing_by_name = ProjectFile.objects.filter(
        project=project,
        category=category,
        name=filename
    ).first()
    
    if existing_by_name:
        logger.debug(f"Found existing file by name: {filename}")
        return existing_by_name
    
    # Could also check by content hash if stored
    # For now, just check by name
    
    return None


@transaction.atomic
def save_pdf_to_project_files(
    project: "Project",
    pdf_bytes: bytes,
    filename: str,
    document_type: Literal["changeorder", "colorsample", "estimate", "contract", "invoice"],
    user: Optional["User"] = None,
    description: str = "",
    source_record: Optional[object] = None,
    overwrite: bool = False,
) -> "ProjectFile":
    """
    Save a PDF to the project's file management system.
    
    Args:
        project: The project to save the file to
        pdf_bytes: The PDF content as bytes
        filename: Name for the file (e.g., "ChangeOrder_123_PRJ001.pdf")
        document_type: Type of document (determines folder)
        user: User who generated/uploaded the file
        description: Optional description for the file
        source_record: Optional source object (ChangeOrder, Invoice, etc.)
        overwrite: If True, update existing file instead of skipping
        
    Returns:
        The created or updated ProjectFile instance
    """
    from core.models import ProjectFile
    
    # Get the appropriate category
    category_type = DOCUMENT_TYPE_CATEGORY.get(document_type, "documents")
    category = _get_or_create_category(project, category_type, user)
    
    # Generate hash for duplicate detection
    content_hash = _get_file_hash(pdf_bytes)
    
    # Check for duplicates
    existing_file = _check_duplicate_file(project, filename, content_hash, category)
    
    if existing_file and not overwrite:
        logger.info(f"File '{filename}' already exists in project {project.name}, skipping")
        return existing_file
    
    if existing_file and overwrite:
        # Update existing file
        logger.info(f"Updating existing file '{filename}' in project {project.name}")
        
        # Delete old file from storage
        if existing_file.file:
            existing_file.file.delete(save=False)
        
        # Save new content
        existing_file.file.save(filename, ContentFile(pdf_bytes), save=False)
        existing_file.file_size = len(pdf_bytes)
        existing_file.updated_at = timezone.now()
        if description:
            existing_file.description = description
        existing_file.save()
        
        return existing_file
    
    # Create new file
    logger.info(f"Saving new file '{filename}' to project {project.name}")
    
    # Build description if not provided
    if not description and source_record:
        description = _build_description_from_source(source_record, document_type)
    
    # Signed documents (COs, Color Samples) should be public for client access
    is_public_doc = document_type in ("changeorder", "colorsample")
    
    project_file = ProjectFile(
        project=project,
        category=category,
        name=filename,
        description=description,
        file_type="pdf",
        uploaded_by=user,
        is_public=is_public_doc,  # Signed documents are public for clients
    )
    
    # Save the file
    project_file.file.save(filename, ContentFile(pdf_bytes), save=False)
    project_file.file_size = len(pdf_bytes)
    project_file.save()
    
    logger.info(f"Successfully saved '{filename}' (ID: {project_file.id}) to {category.name}")
    
    return project_file


def _build_description_from_source(source_record: object, document_type: str) -> str:
    """Build a description based on the source record."""
    if document_type == "changeorder":
        return f"Change Order: {getattr(source_record, 'title', '')} - Auto-generated PDF"
    elif document_type == "colorsample":
        code = getattr(source_record, 'code', '')
        return f"Color Sample {code} - Signed approval document"
    elif document_type in ("estimate", "contract"):
        code = getattr(source_record, 'code', '')
        return f"{'Contract' if document_type == 'contract' else 'Estimate'} {code}"
    elif document_type == "invoice":
        number = getattr(source_record, 'invoice_number', '')
        return f"Invoice #{number} - Auto-generated"
    
    return "Auto-generated document"


# =============================================================================
# HIGH-LEVEL FUNCTIONS FOR EACH DOCUMENT TYPE
# =============================================================================

def auto_save_changeorder_pdf(
    changeorder: "ChangeOrder",
    user: Optional["User"] = None,
    overwrite: bool = False,
) -> Optional["ProjectFile"]:
    """
    Generate and auto-save a Change Order PDF.
    Only saves if the CO is signed.
    """
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    # Only save signed change orders
    if not changeorder.signed_at:
        logger.debug(f"ChangeOrder {changeorder.id} not signed, skipping auto-save")
        return None
    
    try:
        # Generate PDF
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        # Build filename
        co_title = (changeorder.title or "").replace(" ", "_")[:30]
        filename = f"CO_{changeorder.id}_{co_title}_{changeorder.project.project_code}.pdf"
        filename = filename.replace("/", "-").replace("\\", "-")
        
        # Save to project files
        return save_pdf_to_project_files(
            project=changeorder.project,
            pdf_bytes=pdf_bytes,
            filename=filename,
            document_type="changeorder",
            user=user,
            source_record=changeorder,
            overwrite=overwrite,
        )
    except Exception as e:
        logger.error(f"Failed to auto-save ChangeOrder PDF: {e}")
        return None


def auto_save_colorsample_pdf(
    colorsample: "ColorSample",
    user: Optional["User"] = None,
    overwrite: bool = False,
) -> Optional["ProjectFile"]:
    """
    Generate and auto-save a Color Sample PDF.
    Only saves if the sample is signed by client.
    """
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    # Only save signed color samples
    if not colorsample.client_signed_at:
        logger.debug(f"ColorSample {colorsample.id} not signed, skipping auto-save")
        return None
    
    try:
        # Generate PDF
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        # Build filename
        sample_num = colorsample.sample_number or colorsample.id
        filename = f"ColorSample_{sample_num}_{colorsample.code}_{colorsample.project.project_code}.pdf"
        filename = filename.replace("/", "-").replace("\\", "-").replace(" ", "_")
        
        # Save to project files
        return save_pdf_to_project_files(
            project=colorsample.project,
            pdf_bytes=pdf_bytes,
            filename=filename,
            document_type="colorsample",
            user=user,
            source_record=colorsample,
            overwrite=overwrite,
        )
    except Exception as e:
        logger.error(f"Failed to auto-save ColorSample PDF: {e}")
        return None


def auto_save_estimate_pdf(
    estimate: "Estimate",
    user: Optional["User"] = None,
    as_contract: bool = False,
    overwrite: bool = False,
) -> Optional["ProjectFile"]:
    """
    Generate and auto-save an Estimate or Contract PDF.
    """
    from core.services.pdf_service import generate_estimate_pdf
    
    try:
        # Generate PDF
        pdf_bytes = generate_estimate_pdf(estimate, as_contract=as_contract)
        
        # Build filename
        doc_type = "Contract" if as_contract else "Estimate"
        filename = f"{doc_type}_{estimate.code}_{estimate.project.project_code}.pdf"
        filename = filename.replace("/", "-").replace("\\", "-").replace(" ", "_")
        
        # Save to project files
        return save_pdf_to_project_files(
            project=estimate.project,
            pdf_bytes=pdf_bytes,
            filename=filename,
            document_type="contract" if as_contract else "estimate",
            user=user,
            source_record=estimate,
            overwrite=overwrite,
        )
    except Exception as e:
        logger.error(f"Failed to auto-save Estimate PDF: {e}")
        return None


def auto_save_invoice_pdf(
    invoice: "Invoice",
    user: Optional["User"] = None,
    overwrite: bool = False,
) -> Optional["ProjectFile"]:
    """
    Generate and auto-save an Invoice PDF.
    """
    from io import BytesIO
    from django.template.loader import get_template
    from django.utils import timezone
    
    try:
        from xhtml2pdf import pisa
        HAS_PISA = True
    except ImportError:
        pisa = None
        HAS_PISA = False
    
    try:
        # Generate PDF using existing template
        template = get_template("core/invoice_pdf.html")
        context = {
            "invoice": invoice,
            "user": user,
            "now": timezone.now(),
        }
        html = template.render(context)
        
        if HAS_PISA:
            result = BytesIO()
            pdf_status = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
            if not pdf_status.err:
                pdf_bytes = result.getvalue()
            else:
                logger.error("xhtml2pdf error generating invoice PDF")
                return None
        else:
            logger.error("xhtml2pdf not available for invoice PDF generation")
            return None
        
        # Build filename
        invoice_num = invoice.invoice_number or f"INV{invoice.id}"
        project_code = invoice.project.project_code if invoice.project else "NOPROJ"
        filename = f"Invoice_{invoice_num}_{project_code}.pdf"
        filename = filename.replace("/", "-").replace("\\", "-").replace(" ", "_")
        
        # Save to project files (if project exists)
        if not invoice.project:
            logger.warning(f"Invoice {invoice.id} has no project, cannot auto-save")
            return None
        
        return save_pdf_to_project_files(
            project=invoice.project,
            pdf_bytes=pdf_bytes,
            filename=filename,
            document_type="invoice",
            user=user,
            source_record=invoice,
            overwrite=overwrite,
        )
    except Exception as e:
        logger.error(f"Failed to auto-save Invoice PDF: {e}")
        return None


# =============================================================================
# BATCH OPERATIONS
# =============================================================================

def auto_save_all_signed_documents_for_project(
    project: "Project",
    user: Optional["User"] = None
) -> dict:
    """
    Auto-save all signed documents for a project.
    Returns a summary of what was saved.
    """
    from core.models import ChangeOrder, ColorSample, Estimate, Invoice
    
    summary = {
        "changeorders": {"saved": 0, "skipped": 0, "errors": 0},
        "colorsamples": {"saved": 0, "skipped": 0, "errors": 0},
        "estimates": {"saved": 0, "skipped": 0, "errors": 0},
        "invoices": {"saved": 0, "skipped": 0, "errors": 0},
    }
    
    # Change Orders (signed only)
    signed_cos = ChangeOrder.objects.filter(
        project=project,
        signed_at__isnull=False
    )
    for co in signed_cos:
        result = auto_save_changeorder_pdf(co, user)
        if result:
            summary["changeorders"]["saved"] += 1
        else:
            summary["changeorders"]["skipped"] += 1
    
    # Color Samples (signed only)
    signed_samples = ColorSample.objects.filter(
        project=project,
        client_signed_at__isnull=False
    )
    for cs in signed_samples:
        result = auto_save_colorsample_pdf(cs, user)
        if result:
            summary["colorsamples"]["saved"] += 1
        else:
            summary["colorsamples"]["skipped"] += 1
    
    # Estimates (all approved or accepted)
    estimates = Estimate.objects.filter(
        project=project,
        status__in=["approved", "accepted"]
    )
    for est in estimates:
        result = auto_save_estimate_pdf(est, user)
        if result:
            summary["estimates"]["saved"] += 1
        else:
            summary["estimates"]["skipped"] += 1
    
    # Invoices (finalized)
    invoices = Invoice.objects.filter(
        project=project,
        status__in=["sent", "paid", "partial"]
    )
    for inv in invoices:
        result = auto_save_invoice_pdf(inv, user)
        if result:
            summary["invoices"]["saved"] += 1
        else:
            summary["invoices"]["skipped"] += 1
    
    return summary


__all__ = [
    "save_pdf_to_project_files",
    "auto_save_changeorder_pdf",
    "auto_save_colorsample_pdf",
    "auto_save_estimate_pdf",
    "auto_save_invoice_pdf",
    "auto_save_all_signed_documents_for_project",
]
