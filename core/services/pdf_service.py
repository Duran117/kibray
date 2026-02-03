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


def generate_estimate_pdf_reportlab(estimate, as_contract: bool = False) -> bytes:
    """Generate professional Estimate/Contract PDF using ReportLab."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER,
                           leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#059669'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#374151'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4b5563')
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280')
    )
    
    elements = []
    
    # Title
    doc_type = "SUBCONTRACT AGREEMENT" if as_contract else "ESTIMATE"
    elements.append(Paragraph(f"<b>{doc_type}</b>", title_style))
    elements.append(Paragraph(f"{estimate.code}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Project Info
    project = estimate.project
    info_data = [
        ['Project:', project.name, 'Date:', estimate.created_at.strftime('%Y-%m-%d') if estimate.created_at else '-'],
        ['Address:', project.address or '-', 'Version:', f'v{estimate.version}'],
        ['Client:', str(project.client) if project.client else '-', '', ''],
    ]
    
    info_table = Table(info_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 2*inch])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#6b7280')),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))
    
    # Line Items Header
    elements.append(Paragraph("<b>Scope of Work</b>", header_style))
    
    # Line Items Table
    lines = estimate.lines.select_related('cost_code').all()
    
    table_data = [['Code', 'Description', 'Qty', 'UOM', 'Unit Price', 'Total']]
    
    for line in lines:
        unit_price = line.get_effective_unit_price()
        total = line.direct_cost()
        table_data.append([
            line.cost_code.code if line.cost_code else '-',
            line.description or (line.cost_code.name if line.cost_code else '-'),
            f'{line.qty:.2f}',
            line.unit or 'EA',
            f'${unit_price:,.2f}',
            f'${total:,.2f}'
        ])
    
    if not lines:
        table_data.append(['-', 'No items', '-', '-', '-', '-'])
    
    line_table = Table(table_data, colWidths=[0.8*inch, 2.8*inch, 0.6*inch, 0.6*inch, 1*inch, 1*inch])
    line_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Body rows
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#4b5563')),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        # Alignment
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))
    
    # Summary
    subtotal = sum(line.direct_cost() for line in lines)
    
    # Calculate markups
    total_material = sum(line.qty * line.material_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    total_labor = sum(line.qty * line.labor_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    
    labor_markup = total_labor * (estimate.markup_labor / 100) if estimate.markup_labor else Decimal("0")
    material_markup = total_material * (estimate.markup_material / 100) if estimate.markup_material else Decimal("0")
    overhead = subtotal * (estimate.overhead_pct / 100) if estimate.overhead_pct else Decimal("0")
    profit = subtotal * (estimate.target_profit_pct / 100) if estimate.target_profit_pct else Decimal("0")
    
    grand_total = subtotal + labor_markup + material_markup + overhead + profit
    
    summary_data = [
        ['', 'Direct Costs:', f'${subtotal:,.2f}'],
    ]
    
    if labor_markup > 0:
        summary_data.append(['', f'Labor Markup ({estimate.markup_labor}%):', f'${labor_markup:,.2f}'])
    if material_markup > 0:
        summary_data.append(['', f'Material Markup ({estimate.markup_material}%):', f'${material_markup:,.2f}'])
    if overhead > 0:
        summary_data.append(['', f'Overhead ({estimate.overhead_pct}%):', f'${overhead:,.2f}'])
    if profit > 0:
        summary_data.append(['', f'Profit ({estimate.target_profit_pct}%):', f'${profit:,.2f}'])
    
    summary_data.append(['', 'TOTAL:', f'${grand_total:,.2f}'])
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 2*inch, 1.3*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#6b7280')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Total row bold
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, -1), (-1, -1), colors.HexColor('#059669')),
        ('FONTSIZE', (1, -1), (-1, -1), 11),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#059669')),
    ]))
    elements.append(summary_table)
    
    # Footer
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"<i>Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')}</i>", small_style))
    elements.append(Paragraph(f"<i>Kibray Painting • Licensed & Insured</i>", small_style))
    
    doc.build(elements)
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
        # Use ReportLab directly for reliable PDF generation
        if HAS_REPORTLAB:
            return generate_estimate_pdf_reportlab(estimate, as_contract)
        
        # Fallback to HTML rendering if xhtml2pdf is available
        if HAS_PISA:
            context = _build_estimate_context(estimate, as_contract)
            template_name = "core/contract_signed_pdf.html" if as_contract else "core/estimate_pdf.html"
            template = get_template(template_name)
            html = template.render(context)
            return _render_html_to_pdf(html)
        
        raise RuntimeError("No PDF generation library available")


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


# ============================================================================
# CONTRACT PDF GENERATION
# ============================================================================

def generate_contract_pdf_reportlab(contract: "Contract") -> bytes:
    """
    Generate professional Contract PDF using ReportLab.
    
    This generates a full legal contract with:
    - Company header
    - Contract details
    - Scope of work (from estimate lines)
    - Payment schedule
    - Terms and conditions
    - Signature fields
    """
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=LETTER,
        leftMargin=0.75*inch, 
        rightMargin=0.75*inch,
        topMargin=0.75*inch, 
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#059669'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f2937'),
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'ContractNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#374151'),
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    small_style = ParagraphStyle(
        'ContractSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280')
    )
    
    elements = []
    
    # Get data
    estimate = contract.estimate
    project = contract.project
    lines = estimate.lines.select_related('cost_code').all()
    
    # =========================================================================
    # HEADER
    # =========================================================================
    elements.append(Paragraph("<b>PAINTING SERVICES CONTRACT</b>", title_style))
    elements.append(Paragraph(f"Contract No: {contract.contract_number}", 
                              ParagraphStyle('Center', parent=normal_style, alignment=TA_CENTER)))
    elements.append(Spacer(1, 20))
    
    # =========================================================================
    # PARTIES
    # =========================================================================
    elements.append(Paragraph("<b>PARTIES</b>", section_style))
    
    parties_text = f"""
    This Painting Services Contract ("Contract") is entered into as of {contract.created_at.strftime('%B %d, %Y')} by and between:
    <br/><br/>
    <b>CONTRACTOR:</b><br/>
    {COMPANY_INFO['name']}<br/>
    {COMPANY_INFO['address']}<br/>
    Phone: {COMPANY_INFO['phone']}<br/>
    Email: {COMPANY_INFO['email']}<br/>
    <br/>
    <b>CUSTOMER:</b><br/>
    {project.client or 'N/A'}<br/>
    Project Address: {project.address or 'N/A'}<br/>
    """
    elements.append(Paragraph(parties_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # =========================================================================
    # PROJECT INFORMATION
    # =========================================================================
    elements.append(Paragraph("<b>PROJECT INFORMATION</b>", section_style))
    
    project_data = [
        ['Project Name:', project.name, 'Estimate Code:', estimate.code],
        ['Project Address:', project.address or '-', 'Version:', f'v{estimate.version}'],
        ['Contract Date:', contract.created_at.strftime('%Y-%m-%d'), 'Contract Version:', f'v{contract.version}'],
    ]
    
    project_table = Table(project_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 1.8*inch])
    project_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#6b7280')),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(project_table)
    elements.append(Spacer(1, 16))
    
    # =========================================================================
    # SCOPE OF WORK
    # =========================================================================
    elements.append(Paragraph("<b>SCOPE OF WORK</b>", section_style))
    elements.append(Paragraph(
        "Contractor agrees to perform the following painting and finishing services:",
        normal_style
    ))
    elements.append(Spacer(1, 8))
    
    # Line Items Table
    table_data = [['Code', 'Description', 'Qty', 'Unit', 'Unit Price', 'Total']]
    
    for line in lines:
        unit_price = line.get_effective_unit_price()
        total = line.direct_cost()
        table_data.append([
            line.cost_code.code if line.cost_code else '-',
            (line.description or (line.cost_code.name if line.cost_code else '-'))[:40],
            f'{line.qty:.2f}',
            line.unit or 'EA',
            f'${unit_price:,.2f}',
            f'${total:,.2f}'
        ])
    
    if not lines:
        table_data.append(['-', 'No items specified', '-', '-', '-', '-'])
    
    line_table = Table(table_data, colWidths=[0.7*inch, 2.6*inch, 0.5*inch, 0.5*inch, 0.9*inch, 0.9*inch])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))
    
    # =========================================================================
    # CONTRACT SUM
    # =========================================================================
    elements.append(Paragraph("<b>CONTRACT SUM</b>", section_style))
    
    # Calculate totals
    subtotal = sum(line.direct_cost() for line in lines)
    total_material = sum(
        line.qty * line.material_unit_cost 
        for line in lines 
        if not (line.unit_price and line.unit_price > 0)
    )
    total_labor = sum(
        line.qty * line.labor_unit_cost 
        for line in lines 
        if not (line.unit_price and line.unit_price > 0)
    )
    
    from decimal import Decimal
    labor_markup = total_labor * (estimate.markup_labor / 100) if estimate.markup_labor else Decimal("0")
    material_markup = total_material * (estimate.markup_material / 100) if estimate.markup_material else Decimal("0")
    overhead = subtotal * (estimate.overhead_pct / 100) if estimate.overhead_pct else Decimal("0")
    profit = subtotal * (estimate.target_profit_pct / 100) if estimate.target_profit_pct else Decimal("0")
    
    summary_data = [['', 'Direct Costs:', f'${subtotal:,.2f}']]
    
    if labor_markup > 0:
        summary_data.append(['', f'Labor Markup ({estimate.markup_labor}%):', f'${labor_markup:,.2f}'])
    if material_markup > 0:
        summary_data.append(['', f'Material Markup ({estimate.markup_material}%):', f'${material_markup:,.2f}'])
    if overhead > 0:
        summary_data.append(['', f'Overhead ({estimate.overhead_pct}%):', f'${overhead:,.2f}'])
    if profit > 0:
        summary_data.append(['', f'Profit ({estimate.target_profit_pct}%):', f'${profit:,.2f}'])
    
    summary_data.append(['', 'TOTAL CONTRACT AMOUNT:', f'${contract.total_amount:,.2f}'])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2.2*inch, 1.3*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 0), (1, -2), colors.HexColor('#6b7280')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, -1), (-1, -1), colors.HexColor('#059669')),
        ('FONTSIZE', (1, -1), (-1, -1), 12),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('LINEABOVE', (1, -1), (-1, -1), 1.5, colors.HexColor('#059669')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))
    
    # =========================================================================
    # PAYMENT SCHEDULE
    # =========================================================================
    elements.append(Paragraph("<b>PAYMENT SCHEDULE</b>", section_style))
    
    payment_schedule = contract.payment_schedule or []
    if payment_schedule:
        payment_text = "Customer agrees to pay Contractor according to the following schedule:<br/><br/>"
        for payment in payment_schedule:
            payment_text += f"• <b>{payment['name']}</b>: ${Decimal(payment['amount']):,.2f} ({payment['percentage']}%) - {payment['due_trigger']}<br/>"
        elements.append(Paragraph(payment_text, normal_style))
    else:
        elements.append(Paragraph("Payment terms to be agreed upon separately.", normal_style))
    
    elements.append(Spacer(1, 12))
    
    # =========================================================================
    # TERMS AND CONDITIONS (Abbreviated)
    # =========================================================================
    elements.append(Paragraph("<b>TERMS AND CONDITIONS</b>", section_style))
    
    terms = """
    <b>1. WORK STANDARDS:</b> All work shall be performed in a professional manner consistent with industry standards.
    <br/><br/>
    <b>2. MATERIALS:</b> Contractor shall furnish all materials, equipment, and labor necessary to complete the work.
    <br/><br/>
    <b>3. WARRANTY:</b> Contractor warrants workmanship for a period of ONE (1) YEAR from substantial completion.
    <br/><br/>
    <b>4. INSURANCE:</b> Contractor maintains liability insurance and workers' compensation as required by Colorado law.
    <br/><br/>
    <b>5. CHANGES:</b> Any changes to the scope of work must be agreed upon in writing through a Change Order.
    <br/><br/>
    <b>6. LATE PAYMENT:</b> Unpaid balances accrue interest at 1.5% per month (18% annually).
    <br/><br/>
    <b>7. GOVERNING LAW:</b> This Contract shall be governed by the laws of the State of Colorado.
    """
    elements.append(Paragraph(terms, normal_style))
    
    # Page break before signatures
    elements.append(PageBreak())
    
    # =========================================================================
    # SIGNATURES
    # =========================================================================
    elements.append(Paragraph("<b>SIGNATURES</b>", section_style))
    elements.append(Paragraph(
        "By signing below, both parties agree to be bound by the terms and conditions of this Contract.",
        normal_style
    ))
    elements.append(Spacer(1, 20))
    
    # Signature table
    sig_data = [
        ['CONTRACTOR:', '', 'CUSTOMER:', ''],
        ['', '', '', ''],
        ['Signature: _______________________', '', 'Signature: _______________________', ''],
        ['', '', '', ''],
        [f'Name: {COMPANY_INFO["name"]}', '', f'Name: {project.client or "_______________________"}', ''],
        ['', '', '', ''],
        ['Date: _______________________', '', 'Date: _______________________', ''],
    ]
    
    sig_table = Table(sig_data, colWidths=[2.8*inch, 0.4*inch, 2.8*inch, 0.4*inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sig_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"<i>Contract generated on {timezone.now().strftime('%Y-%m-%d %H:%M')} | "
        f"{COMPANY_INFO['name']} - {COMPANY_INFO['license']}</i>",
        ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    return buffer.getvalue()


def generate_signed_contract_pdf_reportlab(contract: "Contract") -> bytes:
    """
    Generate signed Contract PDF with client signature embedded.
    
    This is similar to the unsigned version but includes:
    - "EXECUTED" watermark
    - Client signature image
    - Signature timestamp
    - IP address for audit
    """
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    import base64
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=LETTER,
        leftMargin=0.75*inch, 
        rightMargin=0.75*inch,
        topMargin=0.75*inch, 
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#059669'),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    executed_style = ParagraphStyle(
        'ExecutedStamp',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#059669'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#059669'),
        borderWidth=2,
        borderPadding=8,
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f2937'),
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'ContractNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#374151'),
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    small_style = ParagraphStyle(
        'ContractSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280')
    )
    
    elements = []
    
    # Get data
    estimate = contract.estimate
    project = contract.project
    lines = estimate.lines.select_related('cost_code').all()
    
    # =========================================================================
    # HEADER WITH EXECUTED STAMP
    # =========================================================================
    elements.append(Paragraph("<b>PAINTING SERVICES CONTRACT</b>", title_style))
    elements.append(Paragraph(f"Contract No: {contract.contract_number}", 
                              ParagraphStyle('Center', parent=normal_style, alignment=TA_CENTER)))
    elements.append(Spacer(1, 10))
    
    # EXECUTED stamp
    executed_text = f"✓ CONTRACT EXECUTED - Signed on {contract.client_signed_at.strftime('%B %d, %Y at %H:%M') if contract.client_signed_at else 'N/A'}"
    elements.append(Paragraph(executed_text, executed_style))
    elements.append(Spacer(1, 16))
    
    # =========================================================================
    # PARTIES (same as unsigned)
    # =========================================================================
    elements.append(Paragraph("<b>PARTIES</b>", section_style))
    
    parties_text = f"""
    This Painting Services Contract ("Contract") is entered into as of {contract.created_at.strftime('%B %d, %Y')} by and between:
    <br/><br/>
    <b>CONTRACTOR:</b><br/>
    {COMPANY_INFO['name']}<br/>
    {COMPANY_INFO['address']}<br/>
    <br/>
    <b>CUSTOMER:</b><br/>
    {project.client or 'N/A'}<br/>
    Project Address: {project.address or 'N/A'}<br/>
    """
    elements.append(Paragraph(parties_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # =========================================================================
    # PROJECT INFO (abbreviated for signed version)
    # =========================================================================
    elements.append(Paragraph("<b>PROJECT INFORMATION</b>", section_style))
    
    project_data = [
        ['Project Name:', project.name, 'Contract Amount:', f'${contract.total_amount:,.2f}'],
        ['Project Address:', project.address or '-', 'Contract Version:', f'v{contract.version}'],
    ]
    
    project_table = Table(project_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 1.8*inch])
    project_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#6b7280')),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#059669')),
    ]))
    elements.append(project_table)
    elements.append(Spacer(1, 16))
    
    # =========================================================================
    # SCOPE OF WORK (abbreviated)
    # =========================================================================
    elements.append(Paragraph("<b>SCOPE OF WORK</b>", section_style))
    
    # Line Items Table (same as unsigned)
    table_data = [['Code', 'Description', 'Qty', 'Unit', 'Unit Price', 'Total']]
    
    for line in lines:
        unit_price = line.get_effective_unit_price()
        total = line.direct_cost()
        table_data.append([
            line.cost_code.code if line.cost_code else '-',
            (line.description or (line.cost_code.name if line.cost_code else '-'))[:40],
            f'{line.qty:.2f}',
            line.unit or 'EA',
            f'${unit_price:,.2f}',
            f'${total:,.2f}'
        ])
    
    if not lines:
        table_data.append(['-', 'No items specified', '-', '-', '-', '-'])
    
    line_table = Table(table_data, colWidths=[0.7*inch, 2.6*inch, 0.5*inch, 0.5*inch, 0.9*inch, 0.9*inch])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 16))
    
    # Total
    elements.append(Paragraph(
        f"<b>TOTAL CONTRACT AMOUNT: ${contract.total_amount:,.2f}</b>",
        ParagraphStyle('Total', parent=normal_style, fontSize=12, textColor=colors.HexColor('#059669'))
    ))
    
    # Page break before signatures
    elements.append(PageBreak())
    
    # =========================================================================
    # SIGNATURE SECTION
    # =========================================================================
    elements.append(Paragraph("<b>EXECUTION</b>", section_style))
    elements.append(Paragraph(
        "This Contract has been executed by both parties as indicated below.",
        normal_style
    ))
    elements.append(Spacer(1, 20))
    
    # Customer signature
    elements.append(Paragraph("<b>CUSTOMER SIGNATURE:</b>", section_style))
    
    # Try to include signature image
    if contract.client_signature:
        try:
            # Read signature file
            contract.client_signature.seek(0)
            sig_bytes = contract.client_signature.read()
            sig_buffer = BytesIO(sig_bytes)
            sig_image = Image(sig_buffer, width=2*inch, height=0.75*inch)
            elements.append(sig_image)
        except Exception:
            elements.append(Paragraph("[Signature on file]", normal_style))
    else:
        elements.append(Paragraph("[Digital signature captured]", normal_style))
    
    elements.append(Spacer(1, 8))
    
    sig_details = f"""
    <b>Signed by:</b> {contract.client_signed_name or 'N/A'}<br/>
    <b>Date/Time:</b> {contract.client_signed_at.strftime('%B %d, %Y at %H:%M:%S %Z') if contract.client_signed_at else 'N/A'}<br/>
    <b>IP Address:</b> {contract.client_ip_address or 'N/A'}
    """
    elements.append(Paragraph(sig_details, small_style))
    
    elements.append(Spacer(1, 20))
    
    # Contractor counter-signature
    elements.append(Paragraph("<b>CONTRACTOR ACCEPTANCE:</b>", section_style))
    
    if contract.contractor_signed_at:
        contractor_sig = f"""
        <b>Accepted by:</b> {COMPANY_INFO['name']}<br/>
        <b>Authorized Representative:</b> {contract.contractor_signed_by.get_full_name() if contract.contractor_signed_by else 'Authorized Representative'}<br/>
        <b>Date/Time:</b> {contract.contractor_signed_at.strftime('%B %d, %Y at %H:%M:%S') if contract.contractor_signed_at else 'N/A'}
        """
    else:
        contractor_sig = f"""
        <b>Accepted by:</b> {COMPANY_INFO['name']}<br/>
        <b>Status:</b> Pending contractor acceptance
        """
    elements.append(Paragraph(contractor_sig, small_style))
    
    # Footer with verification info
    elements.append(Spacer(1, 40))
    
    # Generate document hash for verification
    import hashlib
    hash_data = f"{contract.id}|{contract.contract_number}|{contract.client_signed_at}|{contract.total_amount}"
    doc_hash = hashlib.sha256(hash_data.encode()).hexdigest()[:12].upper()
    
    elements.append(Paragraph(
        f"<i>Document ID: {contract.contract_number} | Verification: {doc_hash}<br/>"
        f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')} | "
        f"{COMPANY_INFO['name']} - {COMPANY_INFO['license']}</i>",
        ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    return buffer.getvalue()


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
    "generate_contract_pdf_reportlab",
    "generate_signed_contract_pdf_reportlab",
    "COMPANY_INFO",
]
