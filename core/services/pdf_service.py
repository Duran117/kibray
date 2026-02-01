"""
Professional PDF Generation Service for Legal Documents

This service provides centralized PDF generation for signed legal documents:
- Change Orders
- Color Samples
- Contracts/Estimates

Features:
- Professional letterhead design
- Digital signature display
- Security watermarks
- Audit trail information
- xhtml2pdf with reportlab fallback
"""

from __future__ import annotations

import base64
import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone

if TYPE_CHECKING:
    from core.models import ChangeOrder, ColorSample, Estimate

logger = logging.getLogger(__name__)

# Try to import xhtml2pdf, fallback to reportlab
try:
    from xhtml2pdf import pisa
    HAS_PISA = True
except ImportError:
    pisa = None
    HAS_PISA = False

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


# Company information for letterhead
COMPANY_INFO = {
    "name": "Kibray Painting",
    "address": "North Carolina, USA",
    "phone": "",
    "email": "info@kibray.com",
    "website": "www.kibray.com",
    "license": "Licensed & Insured",
}


def _generate_document_hash(data: dict) -> str:
    """Generate a verification hash for the document."""
    content = "|".join(str(v) for v in data.values())
    return hashlib.sha256(content.encode()).hexdigest()[:16].upper()


def _get_base64_logo() -> str:
    """Get the company logo as base64 for embedding in PDF."""
    try:
        import os
        logo_path = os.path.join(settings.BASE_DIR, "core", "static", "brand", "logo.svg")
        with open(logo_path, "rb") as f:
            logo_data = f.read()
        return base64.b64encode(logo_data).decode("utf-8")
    except Exception:
        return ""


def _render_html_to_pdf(html: str) -> bytes:
    """Render HTML to PDF using xhtml2pdf or fallback."""
    if HAS_PISA:
        try:
            result = BytesIO()
            pdf_status = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
            if not pdf_status.err:
                return result.getvalue()
        except Exception as e:
            logger.warning(f"xhtml2pdf failed: {e}, trying fallback")
    
    # Fallback to basic reportlab
    if HAS_REPORTLAB:
        return _fallback_pdf_from_html(html)
    
    raise RuntimeError("No PDF generation library available")


def _fallback_pdf_from_html(html: str) -> bytes:
    """Basic PDF generation using reportlab as fallback."""
    import re
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    
    # Strip HTML tags for basic text extraction
    text = re.sub(r'<[^>]+>', '\n', html)
    text = re.sub(r'\n+', '\n', text).strip()
    
    # Simple text rendering
    y = height - inch
    for line in text.split('\n')[:60]:  # Limit lines
        line = line.strip()
        if line:
            c.drawString(inch, y, line[:80])
            y -= 14
            if y < inch:
                c.showPage()
                y = height - inch
    
    c.save()
    return buffer.getvalue()


class PDFDocumentGenerator:
    """Generator for professional legal PDF documents."""
    
    @staticmethod
    def generate_changeorder_pdf(changeorder: "ChangeOrder") -> bytes:
        """Generate a professional PDF for a signed Change Order."""
        # Build context
        context = _build_changeorder_context(changeorder)
        
        # Render template
        template = get_template("core/changeorder_signed_pdf.html")
        html = template.render(context)
        
        return _render_html_to_pdf(html)
    
    @staticmethod
    def generate_colorsample_pdf(colorsample: "ColorSample") -> bytes:
        """Generate a professional PDF for a signed Color Sample."""
        context = _build_colorsample_context(colorsample)
        
        template = get_template("core/colorsample_signed_pdf.html")
        html = template.render(context)
        
        return _render_html_to_pdf(html)
    
    @staticmethod
    def generate_estimate_pdf(estimate: "Estimate", as_contract: bool = False) -> bytes:
        """Generate a professional PDF for an Estimate (optionally as contract)."""
        context = _build_estimate_context(estimate, as_contract)
        
        template_name = "core/contract_signed_pdf.html" if as_contract else "core/estimate_pdf.html"
        template = get_template(template_name)
        html = template.render(context)
        
        return _render_html_to_pdf(html)


def _build_changeorder_context(co: "ChangeOrder") -> dict[str, Any]:
    """Build template context for Change Order PDF."""
    # Calculate document hash for verification
    hash_data = {
        "id": co.id,
        "project": co.project.name,
        "amount": str(co.amount),
        "signed_by": co.signed_by or "",
        "signed_at": co.signed_at.isoformat() if co.signed_at else "",
    }
    doc_hash = _generate_document_hash(hash_data)
    
    # Get signature as base64 if exists
    signature_base64 = ""
    if co.signature_image:
        try:
            co.signature_image.seek(0)
            signature_base64 = base64.b64encode(co.signature_image.read()).decode("utf-8")
        except Exception:
            pass
    
    return {
        "changeorder": co,
        "co": co,
        "project": co.project,
        "company": COMPANY_INFO,
        "document_hash": doc_hash,
        "signature_base64": signature_base64,
        "generation_date": timezone.now(),
        "is_signed": bool(co.signed_at),
        "pricing_display": "Fixed Price" if co.pricing_type == "FIXED" else "Time & Materials",
    }


def _build_colorsample_context(cs: "ColorSample") -> dict[str, Any]:
    """Build template context for Color Sample PDF."""
    hash_data = {
        "id": cs.id,
        "project": cs.project.name,
        "code": cs.code,
        "signed_name": cs.client_signed_name or "",
        "signed_at": cs.client_signed_at.isoformat() if cs.client_signed_at else "",
    }
    doc_hash = _generate_document_hash(hash_data)
    
    signature_base64 = ""
    if cs.client_signature:
        try:
            cs.client_signature.seek(0)
            signature_base64 = base64.b64encode(cs.client_signature.read()).decode("utf-8")
        except Exception:
            pass
    
    sample_image_base64 = ""
    if cs.sample_image:
        try:
            cs.sample_image.seek(0)
            sample_image_base64 = base64.b64encode(cs.sample_image.read()).decode("utf-8")
        except Exception:
            pass
    
    return {
        "colorsample": cs,
        "cs": cs,
        "project": cs.project,
        "company": COMPANY_INFO,
        "document_hash": doc_hash,
        "signature_base64": signature_base64,
        "sample_image_base64": sample_image_base64,
        "generation_date": timezone.now(),
        "is_signed": bool(cs.client_signed_at),
    }


def _build_estimate_context(estimate: "Estimate", as_contract: bool) -> dict[str, Any]:
    """Build template context for Estimate/Contract PDF."""
    lines = estimate.lines.select_related("cost_code").all()
    
    # Calculate totals
    total_labor = Decimal("0")
    total_material = Decimal("0")
    total_other = Decimal("0")
    total_direct_price = Decimal("0")
    
    line_data = []
    for line in lines:
        # Use the effective unit price method from the model
        effective_unit_price = line.get_effective_unit_price()
        line_total = line.qty * effective_unit_price
        
        # Track breakdown for markup calculations
        labor = line.qty * line.labor_unit_cost
        material = line.qty * line.material_unit_cost
        other = line.qty * line.other_unit_cost
        
        # If direct unit_price is used, add it to "other" for markup purposes
        if line.unit_price and line.unit_price > 0:
            total_other += line_total
        else:
            total_labor += labor
            total_material += material
            total_other += other
        
        total_direct_price += line_total
        
        line_data.append({
            "cost_code": line.cost_code.code,
            "description": line.description,
            "qty": line.qty,
            "unit": line.unit,
            "unit_price": effective_unit_price,
            "labor": labor,
            "material": material,
            "other": other,
            "total": line_total,
        })
    
    subtotal = total_direct_price
    
    # Apply markups
    labor_markup = total_labor * (estimate.markup_labor / 100) if estimate.markup_labor else Decimal("0")
    material_markup = total_material * (estimate.markup_material / 100) if estimate.markup_material else Decimal("0")
    overhead = subtotal * (estimate.overhead_pct / 100) if estimate.overhead_pct else Decimal("0")
    profit = subtotal * (estimate.target_profit_pct / 100) if estimate.target_profit_pct else Decimal("0")
    
    grand_total = subtotal + labor_markup + material_markup + overhead + profit
    
    hash_data = {
        "id": estimate.id,
        "code": estimate.code,
        "project": estimate.project.name,
        "total": str(grand_total),
    }
    doc_hash = _generate_document_hash(hash_data)
    
    return {
        "estimate": estimate,
        "project": estimate.project,
        "company": COMPANY_INFO,
        "lines": line_data,
        "totals": {
            "labor": total_labor,
            "material": total_material,
            "other": total_other,
            "subtotal": subtotal,
            "labor_markup": labor_markup,
            "material_markup": material_markup,
            "overhead": overhead,
            "profit": profit,
            "grand_total": grand_total,
        },
        "document_hash": doc_hash,
        "generation_date": timezone.now(),
        "as_contract": as_contract,
        "document_type": "SUBCONTRACT AGREEMENT" if as_contract else "ESTIMATE",
    }


# Convenience functions
def generate_signed_changeorder_pdf(changeorder: "ChangeOrder") -> bytes:
    """Generate PDF for signed Change Order."""
    return PDFDocumentGenerator.generate_changeorder_pdf(changeorder)


def generate_signed_colorsample_pdf(colorsample: "ColorSample") -> bytes:
    """Generate PDF for signed Color Sample."""
    return PDFDocumentGenerator.generate_colorsample_pdf(colorsample)


def generate_estimate_pdf(estimate: "Estimate", as_contract: bool = False) -> bytes:
    """Generate PDF for Estimate or Contract."""
    return PDFDocumentGenerator.generate_estimate_pdf(estimate, as_contract)


__all__ = [
    "PDFDocumentGenerator",
    "generate_signed_changeorder_pdf",
    "generate_signed_colorsample_pdf",
    "generate_estimate_pdf",
    "COMPANY_INFO",
]
