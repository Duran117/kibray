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
    "name": "Kibray Paint & Stain LLC",
    "address": "P.O. Box 25881, Silverthorne, CO 80497",
    "phone": "(970) 333-4872",
    "email": "jduran@kibraypainting.net",
    "website": "kibraypainting.net",
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
            # Handle both local and remote storage (S3, etc.)
            sig_file = co.signature_image
            if hasattr(sig_file, 'open'):
                with sig_file.open('rb') as f:
                    signature_base64 = base64.b64encode(f.read()).decode("utf-8")
            else:
                sig_file.seek(0)
                signature_base64 = base64.b64encode(sig_file.read()).decode("utf-8")
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
            # Handle both local and remote storage (S3, etc.)
            sig_file = cs.client_signature
            if hasattr(sig_file, 'open'):
                with sig_file.open('rb') as f:
                    signature_base64 = base64.b64encode(f.read()).decode("utf-8")
            else:
                sig_file.seek(0)
                signature_base64 = base64.b64encode(sig_file.read()).decode("utf-8")
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
# CONTRACT PDF GENERATION - Full Professional Contract Template
# Based on Colorado Painting Services Contract Template
# ============================================================================

def generate_contract_pdf_reportlab(contract: "Contract") -> bytes:
    """
    Generate professional Contract PDF using ReportLab.
    
    Full legal contract based on Colorado painting services template with:
    - ARTICLE 1: Scope of Work
    - ARTICLE 2: Contract Sum and Payment Terms
    - ARTICLE 3: Project Schedule
    - ARTICLE 4: Changes and Additions
    - ARTICLE 5: Warranties
    - ARTICLE 6: Insurance and Liability
    - ARTICLE 7: Liens and Payment Protection
    - ARTICLE 8: Permits and Compliance
    - ARTICLE 9: Site Conditions and Cleanup
    - ARTICLE 10: Termination
    - ARTICLE 11: Dispute Resolution
    - ARTICLE 12: Indemnification
    - ARTICLE 13: General Provisions
    - ARTICLE 14: Colorado-Specific Provisions
    - Acknowledgements and Signatures
    """
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    from decimal import Decimal
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=LETTER,
        leftMargin=0.6*inch, 
        rightMargin=0.6*inch,
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#059669'),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    article_style = ParagraphStyle(
        'ArticleHeader',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#059669'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=9,
        textColor=colors.HexColor('#1f2937'),
        spaceBefore=8,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'ContractNormal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#374151'),
        alignment=TA_JUSTIFY,
        spaceAfter=4,
        leading=10
    )
    
    bold_style = ParagraphStyle(
        'ContractBold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    small_style = ParagraphStyle(
        'ContractSmall',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#6b7280'),
        leading=9
    )
    
    italic_style = ParagraphStyle(
        'ContractItalic',
        parent=small_style,
        fontName='Helvetica-Oblique'
    )
    
    elements = []
    
    # Get data
    estimate = contract.estimate
    project = contract.project
    lines = estimate.lines.select_related('cost_code').all()
    client = project.client
    
    # Get client info
    client_name = str(client) if client else "{{CUSTOMER_NAME}}"
    client_address = getattr(client, 'address', None) or "{{CUSTOMER_ADDRESS}}"
    client_city_state = getattr(client, 'city_state_zip', None) or "{{CUSTOMER_CITY_STATE_ZIP}}"
    client_phone = getattr(client, 'phone', None) or "{{CUSTOMER_PHONE}}"
    client_email = getattr(client, 'email', None) or "{{CUSTOMER_EMAIL}}"
    
    # =========================================================================
    # HEADER - PAINTING SERVICES CONTRACT
    # =========================================================================
    elements.append(Paragraph("<b>PAINTING SERVICES CONTRACT</b>", title_style))
    elements.append(Spacer(1, 4))
    
    header_data = [
        [f"Contract Number: {contract.contract_number}", f"Date: {contract.created_at.strftime('%B %d, %Y')}"]
    ]
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))
    
    # =========================================================================
    # PARTIES TO THIS AGREEMENT
    # =========================================================================
    elements.append(Paragraph("<b>PARTIES TO THIS AGREEMENT</b>", article_style))
    
    parties_text = f"""
    <b>CONTRACTOR:</b> {COMPANY_INFO['name']}<br/>
    {COMPANY_INFO['address']}<br/>
    Phone: {COMPANY_INFO['phone']} | Email: {COMPANY_INFO['email']}<br/>
    <i>Licensed &amp; Insured</i><br/><br/>
    <b>CUSTOMER:</b> {client_name}<br/>
    {client_address}<br/>
    {client_city_state}<br/>
    Phone: {client_phone} | Email: {client_email}<br/><br/>
    <b>PROJECT:</b> {project.name}<br/>
    Location: {project.address or 'TBD'}<br/>
    Estimate Reference: {estimate.code} (v{estimate.version})
    """
    elements.append(Paragraph(parties_text, normal_style))
    elements.append(Spacer(1, 8))
    
    # Recitals
    recitals = """
    <b>RECITALS:</b> Customer desires to engage Contractor to provide professional painting services at 
    the Project Location. Contractor agrees to perform such services in accordance with the terms 
    of this Contract. In consideration of the mutual covenants and agreements contained herein, 
    the parties agree as follows:
    """
    elements.append(Paragraph(recitals, normal_style))
    elements.append(Spacer(1, 8))
    
    # =========================================================================
    # ARTICLE 1: SCOPE OF WORK
    # =========================================================================
    elements.append(Paragraph("ARTICLE 1: SCOPE OF WORK", article_style))
    
    # 1.1 Services
    elements.append(Paragraph(
        f"<b>1.1 Services.</b> Contractor agrees to provide professional painting services as detailed in Estimate "
        f"{estimate.code}, which is incorporated herein by reference. The work includes:",
        normal_style
    ))
    
    # Scope table
    scope_data = [['Code', 'Description', 'Qty', 'Unit', 'Unit Price', 'Total']]
    subtotal = Decimal("0")
    
    for line in lines:
        unit_price = line.get_effective_unit_price()
        total = line.direct_cost()
        subtotal += total
        scope_data.append([
            line.cost_code.code if line.cost_code else '-',
            (line.description or (line.cost_code.name if line.cost_code else '-'))[:50],
            f'{line.qty:.1f}',
            line.unit or 'EA',
            f'${unit_price:,.2f}',
            f'${total:,.2f}'
        ])
    
    if not lines:
        scope_data.append(['-', 'See attached scope document', '-', '-', '-', '-'])
    
    scope_table = Table(scope_data, colWidths=[0.7*inch, 2.8*inch, 0.5*inch, 0.5*inch, 0.8*inch, 0.9*inch])
    scope_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(scope_table)
    elements.append(Spacer(1, 8))
    
    # 1.2 Standards
    elements.append(Paragraph(
        "<b>1.2 Standards.</b> All work will be performed in a professional and workmanlike manner "
        "according to industry standards, manufacturer specifications, and accepted painting practices. "
        "Contractor will use quality materials suitable for their intended purpose and Colorado climate conditions.",
        normal_style
    ))
    
    # 1.3 Surface Preparation
    elements.append(Paragraph(
        "<b>1.3 Surface Preparation.</b> Contractor will perform surface preparation necessary for proper "
        "paint adhesion, including: - Cleaning surfaces to remove dirt, chalk, and debris - Scraping loose "
        "or peeling paint - Sanding to smooth surfaces and feather edges - Patching minor cracks and "
        "holes (less than 2 inches) - Priming bare surfaces and stains",
        normal_style
    ))
    
    # 1.4 Excluded Work
    elements.append(Paragraph(
        "<b>IMPORTANT:</b> Contractor is NOT responsible for pre-existing conditions including: structural "
        "defects, water damage, mold, rot, extensive plaster/drywall repairs (requiring more than minor "
        "patching), lead paint abatement, asbestos removal, or underlying substrate failure. If such "
        "conditions are discovered, Contractor will promptly notify Customer. Work will not proceed in "
        "affected areas without Customer's written authorization and agreement on additional costs.",
        normal_style
    ))
    
    # 1.4 Excluded Work List
    elements.append(Paragraph(
        "<b>1.4 Excluded Work.</b> Unless specifically included in Scope of Work, the following are excluded: "
        "- Moving furniture (Customer must move or protect furnishings) - Extensive surface repairs "
        "beyond minor patching - Structural, plumbing, or electrical repairs - Repair of damage caused "
        "by water intrusion, settling, or structural movement - Window washing or cleaning beyond "
        "paint removal - Landscaping restoration or lawn repair - Removal of wallpaper (unless "
        "specifically included)",
        normal_style
    ))
    
    # 1.5 Customer's Responsibility
    elements.append(Paragraph(
        "<b>1.5 Customer's Responsibility.</b> Customer shall: - Remove or protect all furniture, window "
        "treatments, wall hangings, and personal items - Provide clear access to all work areas - Secure "
        "pets during work hours - Provide access to water and electricity at no cost - Make color "
        "selections in a timely manner to avoid delays",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 2: CONTRACT SUM AND PAYMENT TERMS
    # =========================================================================
    elements.append(Paragraph("ARTICLE 2: CONTRACT SUM AND PAYMENT TERMS", article_style))
    
    # Calculate totals
    labor_markup = subtotal * (estimate.markup_labor / 100) if estimate.markup_labor else Decimal("0")
    material_markup = subtotal * (estimate.markup_material / 100) if estimate.markup_material else Decimal("0")
    overhead = subtotal * (estimate.overhead_pct / 100) if estimate.overhead_pct else Decimal("0")
    profit = subtotal * (estimate.target_profit_pct / 100) if estimate.target_profit_pct else Decimal("0")
    
    elements.append(Paragraph(
        f"<b>2.1 Contract Sum.</b> The total Contract Sum is <b>${contract.total_amount:,.2f}</b> which includes: "
        f"- All labor and supervision - All materials (paint, primers, caulk, etc.) - Equipment and tools - "
        f"Colorado sales tax (where applicable) - All items specified in Estimate {estimate.code}",
        normal_style
    ))
    
    # 2.2 Payment Schedule
    elements.append(Paragraph("<b>2.2 Payment Schedule.</b>", normal_style))
    
    payment_schedule = contract.payment_schedule or []
    if payment_schedule:
        payment_text = ""
        for payment in payment_schedule:
            amount = Decimal(payment['amount'])
            payment_text += f"• <b>{payment['name']}</b>: ${amount:,.2f} ({payment['percentage']}%) - {payment['due_trigger']}<br/>"
        elements.append(Paragraph(payment_text, normal_style))
    
    # 2.3 Payment Methods
    elements.append(Paragraph(
        "<b>2.3 Payment Methods.</b> Contractor accepts: - Personal checks (payable to \"Kibray Paint &amp; Stain "
        "LLC\") - Cash - Credit cards: Visa, MasterCard, American Express (3% processing fee) - "
        "ACH/Bank transfer (details provided upon request)",
        normal_style
    ))
    
    # 2.4 Payment Terms
    elements.append(Paragraph(
        "<b>2.4 Payment Terms.</b> All payments are due within <b>three (3) business days</b> of invoice date. "
        f"Invoices will be sent to {client_email} and can also be paid online at [payment portal].",
        normal_style
    ))
    
    # 2.5 Late Payment
    elements.append(Paragraph(
        "<b>2.5 Late Payment.</b> Payments not received within ten (10) days of due date will incur: - Late fee "
        "of <b>1.5% per month</b> (18% APR) on outstanding balance - Contractor reserves the right to "
        "suspend work if payment is more than 15 days past due - Customer remains responsible for "
        "late fees even if work is suspended",
        normal_style
    ))
    
    # 2.6 Retainage
    elements.append(Paragraph(
        "<b>2.6 Retainage.</b> Per Colorado law (HB21-1167), Customer may withhold up to <b>5% of completed "
        "work</b> until final completion and acceptance. Final payment including retainage is due within "
        "<b>seven (7) days</b> of substantial completion.",
        normal_style
    ))
    
    # 2.7 Collection Costs
    elements.append(Paragraph(
        "<b>2.7 Collection Costs.</b> If legal action is required to collect payment, Customer agrees to pay: - All "
        "reasonable attorney fees - Court costs and filing fees - Collection agency fees - Interest at <b>12% "
        "per annum</b> (per C.R.S. §38-22-101(5)) - Cost of filing and enforcing mechanic's lien",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 3: PROJECT SCHEDULE
    # =========================================================================
    elements.append(Paragraph("ARTICLE 3: PROJECT SCHEDULE", article_style))
    
    # Format dates or show placeholder
    start_date_str = contract.start_date.strftime('%B %d, %Y') if contract.start_date else "To Be Determined"
    completion_date_str = contract.completion_date.strftime('%B %d, %Y') if contract.completion_date else "To Be Determined"
    
    elements.append(Paragraph(
        f"<b>3.1 Commencement and Completion.</b> - Start Date: <b>{start_date_str}</b> - Substantial "
        f"Completion: <b>{completion_date_str}</b><br/><br/>"
        "These dates are <b>estimates</b> and may be adjusted for weather, site conditions, or other factors "
        "beyond Contractor's control. \"Substantial completion\" means all work is complete except "
        "for minor punchlist items that do not prevent normal use.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>3.2 Weather Dependencies.</b> Painting requires specific environmental conditions:<br/>"
        "<b>Exterior Work:</b> - Temperature: 50°F - 90°F - No precipitation within 24 hours before or 24-48 "
        "hours after application - Humidity: Below 85% - Wind: Below 15 mph (for spray applications)<br/>"
        "<b>Interior Work:</b> - Adequate ventilation - Climate control (heating/cooling operational) - "
        "Humidity below 70%<br/>"
        "Schedule will be extended for unsuitable weather <b>at no additional cost</b> to Customer.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>3.3 Permissible Delays.</b> The completion date will be extended for: (a) Adverse weather "
        "conditions unsuitable for painting (b) Acts or omissions of Customer or Customer's agents "
        "(c) Changes in scope of work (d) Delays in Customer's color or material selections "
        "(e) Unforeseen site conditions requiring additional work (f) Labor disputes, strikes, or material shortages "
        "(g) Fire, casualty, or acts of God (h) Discovery of hazardous materials "
        "(i) Governmental restrictions or delays in permits (j) Other causes beyond Contractor's reasonable control",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>3.4 Access.</b> Customer must provide access to work areas during normal business hours "
        "(Monday-Friday, 8:00 AM - 5:00 PM). Repeated failure to provide access may result in schedule "
        "delays and additional mobilization charges.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 4: CHANGES AND ADDITIONS
    # =========================================================================
    elements.append(Paragraph("ARTICLE 4: CHANGES AND ADDITIONS", article_style))
    
    elements.append(Paragraph(
        "<b>4.1 Change Orders Required.</b> <b>ALL changes</b> to scope, schedule, or price must be documented "
        "in a <b>written Change Order</b> signed by both parties before work commences. Verbal agreements "
        "are not binding.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>4.2 Customer-Requested Changes.</b> Customer may request changes, but Contractor is not "
        "obligated to perform work beyond original scope without: - Contractor agrees to changes - Contractor "
        "will provide written estimate - Customer must approve in writing before work begins - Contract "
        "Sum and schedule will be adjusted accordingly",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>4.3 Additional Work Pricing.</b> Work performed outside original scope without written Change "
        "Order will be billed at: - Labor: <b>$85/hour</b> (includes supervision) - Materials: <b>Cost + 20% "
        "markup</b> - Equipment rental: <b>Actual cost + 15%</b>",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>4.4 Concealed Conditions.</b> If Contractor encounters concealed or unforeseen conditions (rot, "
        "mold, structural defects, etc.), Contractor will: - Stop work in affected area - Notify Customer "
        "within 24 hours - Provide estimate for addressing condition - Await Customer's written "
        "authorization before proceeding",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>4.5 Customer Color Changes.</b> Customer may change colors before application begins at no "
        "charge. Color changes after application has begun will be charged as additional work at rates in "
        "Section 4.3.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 5: WARRANTIES
    # =========================================================================
    elements.append(Paragraph("ARTICLE 5: WARRANTIES", article_style))
    
    elements.append(Paragraph(
        "<b>5.1 Workmanship Warranty.</b> Contractor warrants that all work will be: - Performed in a "
        "professional and workmanlike manner - Free from defects in workmanship for <b>ONE (1) YEAR</b> "
        "from date of substantial completion - Completed using proper techniques and industry standards",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>5.2 Materials Warranty.</b> Paint and materials are warranted by their respective "
        "manufacturers. Contractor will provide manufacturer warranty documentation. <b>Contractor "
        "does not warrant materials beyond manufacturer's warranty.</b>",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>5.3 Warranty Exclusions.</b> This warranty does NOT cover: - Damage caused by Customer or "
        "third parties - Normal wear and tear - Failure to properly maintain painted surfaces - Damage "
        "from water intrusion, leaks, or moisture - Settling, cracking, or movement of structure - "
        "Improper ventilation or extreme environmental conditions - Color fading from UV exposure "
        "(exterior) - Damage from cleaning with harsh chemicals - Areas painted over Customer-"
        "supplied paint - Pre-existing conditions or defects in substrate - Acts of God, vandalism, or "
        "casualty",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>5.4 Warranty Claims.</b> To make a warranty claim, Customer must: - Notify Contractor <b>in "
        "writing within 30 days</b> of discovering defect - Provide photos documenting the issue - Provide "
        "access for Contractor to inspect - Allow Contractor reasonable time to remedy",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>5.5 Warranty Remedy.</b> Contractor's <b>sole obligation</b> under this warranty is to repair or "
        "repaint defective work <b>at no charge</b> for labor. Customer pays for any materials needed (paint, "
        "primer). <b>Warranty is non-transferable</b> unless Contractor provides written consent.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>5.6 Limitation.</b> THIS WARRANTY IS IN LIEU OF ALL OTHER WARRANTIES, EXPRESS OR "
        "IMPLIED, INCLUDING ANY IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS "
        "FOR A PARTICULAR PURPOSE.",
        bold_style
    ))
    
    # =========================================================================
    # ARTICLE 6: INSURANCE AND LIABILITY
    # =========================================================================
    elements.append(Paragraph("ARTICLE 6: INSURANCE AND LIABILITY", article_style))
    
    elements.append(Paragraph(
        "<b>6.1 Contractor's Insurance.</b> Contractor maintains: - <b>General Liability</b>: $1,000,000 per "
        "occurrence / $2,000,000 aggregate - <b>Automobile Liability</b>: $1,000,000 combined single limit - "
        "<b>Workers' Compensation</b>: Statutory limits for all employees - <b>Umbrella Liability</b>: $1,000,000 "
        "occurrence/aggregate<br/>Certificates of insurance available upon request.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>6.2 Customer's Insurance.</b> Customer is responsible for maintaining adequate insurance on "
        "property and contents. <b>Contractor is not responsible for damage to items not properly "
        "protected or removed by Customer.</b>",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>6.3 Limitation of Liability.</b> TO THE MAXIMUM EXTENT PERMITTED BY COLORADO LAW: "
        "- Contractor's total liability under this Contract shall not exceed the <b>total Contract Sum</b> - "
        "Contractor shall not be liable for indirect, incidental, consequential, or punitive damages - "
        "Contractor shall not be liable for lost profits, lost business, or loss of use - Customer's remedy is "
        "limited to repair or replacement of defective work",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>6.4 Property Protection.</b> Contractor will: - Use drop cloths and protective coverings - Protect "
        "floors, fixtures, and surfaces not being painted - Remove paint splatters and overspray - Clean "
        "work areas daily<br/><b>Contractor is not responsible for damage to items Customer failed to remove or "
        "protect.</b>",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 7: LIENS AND PAYMENT PROTECTION
    # =========================================================================
    elements.append(Paragraph("ARTICLE 7: LIENS AND PAYMENT PROTECTION", article_style))
    
    elements.append(Paragraph(
        "<b>7.1 Mechanic's Lien Rights.</b> Under Colorado law (C.R.S. §38-22-101 et seq.), <b>Contractor has "
        "the right to file a mechanic's lien</b> against the property for unpaid amounts. This is "
        "Contractor's legal protection for payment.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>7.2 Notice to Owner.</b> COLORADO LAW NOTICE: Contractor has mechanic's lien rights. "
        "Failure to pay may result in a lien against the property. Customer acknowledges receiving this "
        "notice as required by law.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>7.3 Lien Waiver.</b> Upon receipt of <b>full payment</b>, Contractor will provide Customer with a final "
        "lien waiver and release.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>7.4 Subordinate Liens.</b> If Contractor files a lien, Customer agrees to subordinate any refinance "
        "or sale until lien is satisfied.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>7.5 Owner Verification.</b> Customer represents and warrants that: - Customer is the legal owner "
        "of the property, OR - Customer has obtained owner's written consent to perform work<br/>"
        "If Customer is not the owner, Customer agrees to <b>indemnify and hold Contractor harmless</b> "
        "from any claims by property owner.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 8: PERMITS AND COMPLIANCE
    # =========================================================================
    elements.append(Paragraph("ARTICLE 8: PERMITS AND COMPLIANCE", article_style))
    
    elements.append(Paragraph(
        "<b>8.1 Permits.</b> <b>Painting does not require permits</b> in most Colorado jurisdictions (per "
        "research). If permits are required, Customer is responsible for obtaining and paying for "
        "permits.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>8.2 HOA Approval.</b> If property is in an HOA, <b>Customer is responsible</b> for obtaining HOA "
        "approval for colors and work. Contractor is not responsible for delays due to HOA requirements.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>8.3 Code Compliance.</b> All work will comply with applicable Colorado building codes and local "
        "ordinances.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>8.4 Lead Paint.</b> If structure was built before 1978, it may contain lead paint. Contractor is <b>EPA "
        "RRP certified</b> [if applicable - verify]. Customer acknowledges receipt of EPA lead paint "
        "pamphlet. If lead paint testing or abatement is required, this is <b>not included</b> in Contract Sum.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 9: SITE CONDITIONS AND CLEANUP
    # =========================================================================
    elements.append(Paragraph("ARTICLE 9: SITE CONDITIONS AND CLEANUP", article_style))
    
    elements.append(Paragraph(
        "<b>9.1 Daily Cleanup.</b> Contractor will: - Maintain reasonably clean work site - Remove debris and "
        "materials daily - Sweep work areas - Dispose of waste properly",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>9.2 Final Cleanup.</b> Upon completion, Contractor will: - Remove all equipment, materials, and "
        "debris - Clean paint splatters and overspray - Sweep and vacuum work areas - Touch up as "
        "needed",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>9.3 Customer's Cleanup.</b> Customer is responsible for: - Final deep cleaning - Window "
        "washing - Landscaping restoration - Lawn repair from equipment access",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>9.4 Disposal.</b> Contractor will dispose of paint waste in accordance with Colorado "
        "environmental regulations.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 10: TERMINATION
    # =========================================================================
    elements.append(Paragraph("ARTICLE 10: TERMINATION", article_style))
    
    elements.append(Paragraph(
        "<b>10.1 Termination by Customer.</b> Customer may terminate this Contract:<br/><br/>"
        "<b>(A) For Convenience:</b> Upon <b>seven (7) days' written notice</b>. Customer may terminate for "
        "any reason. Upon termination, Customer shall pay: - All work completed to date (prorated) - All "
        "materials purchased and delivered - Demobilization costs - <b>20% of unearned Contract Sum</b> "
        "as liquidated damages for lost profit<br/><br/>"
        "<b>(B) For Cause:</b> If Contractor: - Abandons the work for more than 10 days without cause - Fails "
        "to perform work according to Contract after written notice and 10 days to cure - Breaches "
        "material term after notice and opportunity to cure<br/>"
        "If terminated for cause, Customer pays only for work completed.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>10.2 Termination by Contractor.</b> Contractor may terminate this Contract <b>immediately</b> upon "
        "written notice if: - Customer fails to make payment when due and fails to cure within <b>5 days</b> of "
        "notice - Customer repeatedly fails to provide site access - Customer interferes with Contractor's "
        "work - Customer breaches material term of Contract - Conditions make work unsafe or "
        "impossible<br/><br/>"
        "Upon termination by Contractor, Customer shall <b>immediately</b> pay: - All work completed to "
        "date - All materials purchased and delivered - Demobilization costs - <b>15% of unearned "
        "Contract Sum</b> as liquidated damages - All collection costs including attorney fees",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>10.3 Effect of Termination.</b> Upon termination: - Contractor will cease work - Contractor will "
        "remove equipment and materials - Contractor will secure work area - Customer will make final "
        "payment within 7 days - Both parties released from further obligations except payment",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 11: DISPUTE RESOLUTION
    # =========================================================================
    elements.append(Paragraph("ARTICLE 11: DISPUTE RESOLUTION", article_style))
    
    elements.append(Paragraph(
        "<b>11.1 Negotiation First.</b> Before initiating legal proceedings, parties agree to attempt to resolve "
        "disputes through good-faith negotiation for <b>fifteen (15) days</b>.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>11.2 Mediation.</b> If negotiation fails, parties may agree to <b>non-binding mediation</b>. Mediation "
        "costs split equally. Mediation will be conducted in Summit County, Colorado.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>11.3 Legal Action.</b> If mediation fails or is declined, either party may pursue legal action in: - "
        "State or federal courts in <b>Summit County, Colorado</b> - Small claims court (if claim is within "
        "jurisdictional limits)",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>11.4 Jury Waiver.</b> <b>BOTH PARTIES WAIVE RIGHT TO TRIAL BY JURY</b> for any claims arising "
        "from this Contract.",
        bold_style
    ))
    
    elements.append(Paragraph(
        "<b>11.5 Attorney Fees.</b> <b>The prevailing party</b> in any legal action shall recover: - Reasonable "
        "attorney fees - Court costs - Expert witness fees - All costs of litigation",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>11.6 Venue.</b> Exclusive venue for any legal action is <b>Summit County, Colorado</b>.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 12: INDEMNIFICATION
    # =========================================================================
    elements.append(Paragraph("ARTICLE 12: INDEMNIFICATION", article_style))
    
    elements.append(Paragraph(
        "<b>12.1 Contractor's Indemnity.</b> Contractor shall indemnify and hold harmless Customer from "
        "claims arising from: - Contractor's negligence in performing work - Bodily injury caused by "
        "Contractor's employees or agents - Property damage caused by Contractor's negligence<br/>"
        "<b>BUT ONLY</b> to the extent of Contractor's insurance coverage and only for Contractor's "
        "own negligence.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>12.2 Customer's Indemnity.</b> Customer shall indemnify and hold harmless Contractor from: - "
        "Customer's breach of this Contract - Customer's negligence or willful misconduct - Defects in "
        "the property not caused by Contractor - Claims by property owner (if Customer is not owner) - "
        "Liens or encumbrances on property existing before this Contract - Damage to items Customer "
        "failed to remove or protect - Injury to persons on property not caused by Contractor",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>12.3 Mutual Release.</b> Neither party shall be liable for consequential, indirect, or punitive "
        "damages.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 13: GENERAL PROVISIONS
    # =========================================================================
    elements.append(Paragraph("ARTICLE 13: GENERAL PROVISIONS", article_style))
    
    elements.append(Paragraph(
        f"<b>13.1 Entire Agreement.</b> This Contract, including incorporated Estimate "
        f"{estimate.code}, constitutes the <b>entire agreement</b> between parties. All prior "
        f"negotiations, representations, or agreements are superseded.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.2 Amendments.</b> This Contract may be modified <b>only by written Change Order</b> signed by "
        "both parties.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.3 Governing Law.</b> This Contract shall be governed by the <b>laws of the State of Colorado</b> "
        "without regard to conflicts of law principles.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.4 Severability.</b> If any provision is held invalid or unenforceable, remaining provisions "
        "remain in full force.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.5 Waiver.</b> Failure to enforce any provision does not waive right to enforce it in the future.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.6 Assignment.</b> - Contractor may assign this Contract without Customer consent - "
        "<b>Customer may NOT assign</b> without Contractor's written consent",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.7 Independent Contractor.</b> Contractor is an independent contractor, not an employee. "
        "Contractor responsible for all employment taxes, workers' compensation, and insurance for its "
        "employees.",
        normal_style
    ))
    
    elements.append(Paragraph(
        f"<b>13.8 Notices.</b> All notices must be in writing and sent to:<br/>"
        f"<b>To Contractor:</b><br/>"
        f"{COMPANY_INFO['name']}<br/>"
        f"{COMPANY_INFO['address']}<br/>"
        f"Email: {COMPANY_INFO['email']}<br/><br/>"
        f"<b>To Customer:</b><br/>"
        f"{client_name}<br/>"
        f"{client_address}<br/>"
        f"{client_email}<br/>"
        f"Email constitutes valid notice if sent to above addresses.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.9 Survival.</b> Articles 5 (Warranties), 7 (Liens), 8 (Permits), 10 (Termination), 11 (Disputes), "
        "and 12 (Indemnification) survive completion or termination.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.10 Force Majeure.</b> Neither party liable for delays or failure to perform due to: acts of God, "
        "fire, flood, earthquake, war, terrorism, government action, epidemic, pandemic, labor disputes, "
        "or other causes beyond reasonable control.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.11 Headings.</b> Article headings are for convenience only and do not affect interpretation.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.12 Counterparts.</b> This Contract may be executed in counterparts, each constituting an "
        "original.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>13.13 Electronic Signatures.</b> Electronic signatures are valid and binding.",
        normal_style
    ))
    
    # =========================================================================
    # ARTICLE 14: COLORADO-SPECIFIC PROVISIONS
    # =========================================================================
    elements.append(Paragraph("ARTICLE 14: COLORADO-SPECIFIC PROVISIONS", article_style))
    
    elements.append(Paragraph(
        "<b>14.1 Required Contracts in Writing.</b> Per C.R.S. §38-22-101(3), contracts over $500 must be in "
        "writing. This Contract satisfies that requirement.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>14.2 Retainage Limits.</b> Per HB21-1167, retainage on private projects limited to <b>5% maximum</b>.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>14.3 Mechanic's Lien Notice.</b> REQUIRED NOTICE UNDER C.R.S. §38-22-101: Contractor has "
        "the right to file a mechanic's lien for unpaid work. Customer acknowledges this notice.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>14.4 Right to Rescind.</b> IF THIS CONTRACT WAS SIGNED AT CUSTOMER'S RESIDENCE and "
        "Customer did not initiate contact for this specific project, Customer may have a <b>three (3) "
        "business day right to cancel</b> under Colorado Consumer Protection Act (C.R.S. §6-1-105). To "
        "cancel, Customer must notify Contractor in writing within 3 business days.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>14.5 No Waiver of Lien Rights on Retainage.</b> Per Colorado law, final payment does not waive "
        "lien rights for retainage withheld.",
        normal_style
    ))
    
    elements.append(Paragraph(
        "<b>14.6 Interest on Unpaid Amounts.</b> Per C.R.S. §38-22-101(5), unpaid amounts accrue interest "
        "at <b>12% per annum or contract rate, whichever is higher</b>.",
        normal_style
    ))
    
    # Spacer before signatures (no page break - flows naturally)
    elements.append(Spacer(1, 24))
    
    # =========================================================================
    # ACKNOWLEDGEMENTS AND SIGNATURES
    # =========================================================================
    elements.append(Paragraph("ACKNOWLEDGEMENTS AND SIGNATURES", article_style))
    
    elements.append(Paragraph(
        "<b>BY SIGNING BELOW, BOTH PARTIES ACKNOWLEDGE THAT:</b>",
        bold_style
    ))
    
    ack_items = [
        "They have read and understand all terms of this Contract",
        "They have had opportunity to consult with legal counsel",
        "They agree to be bound by all terms and conditions",
        "This Contract represents the complete agreement",
        "Customer acknowledges Contractor's mechanic's lien rights",
        "Customer received Lead Paint Pamphlet (if applicable)",
        "Customer received copy of this signed Contract"
    ]
    
    ack_text = ""
    for i, item in enumerate(ack_items, 1):
        ack_text += f"{i}. {item}<br/>"
    elements.append(Paragraph(ack_text, normal_style))
    elements.append(Spacer(1, 20))
    
    # Signature table
    sig_data = [
        ['CONTRACTOR:', '', 'CUSTOMER:', ''],
        [f'{COMPANY_INFO["name"]}', '', f'{client_name}', ''],
        ['', '', '', ''],
        ['By: _______________________________', '', 'By: _______________________________', ''],
        ['', '', '', ''],
        ['Date: _____________', '', 'Date: _____________', ''],
        ['', '', '', ''],
        ['Jesus Perez Duran, President', '', f'Print Name: ___________________', ''],
    ]
    
    sig_table = Table(sig_data, colWidths=[3*inch, 0.5*inch, 3*inch, 0.5*inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
        ('FONTNAME', (2, 1), (2, 1), 'Helvetica'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 20))
    
    # Acceptance
    elements.append(Paragraph(
        f"<b>ACCEPTANCE:</b> Customer acknowledges receipt of signed copy of this Contract and "
        f"incorporated Estimate {estimate.code}.",
        normal_style
    ))
    elements.append(Spacer(1, 20))
    
    # Legal disclaimer
    elements.append(Paragraph(
        "<i>This contract template should be reviewed by a Colorado-licensed attorney before use. Laws "
        "change and individual circumstances vary. This template is for informational purposes and does "
        "not constitute legal advice.</i>",
        italic_style
    ))
    
    # Footer
    elements.append(Spacer(1, 20))
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
            # Handle both local and remote storage (S3, etc.)
            sig_file = contract.client_signature
            if hasattr(sig_file, 'open'):
                with sig_file.open('rb') as f:
                    sig_bytes = f.read()
            else:
                sig_file.seek(0)
                sig_bytes = sig_file.read()
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


def generate_changeorder_pdf_reportlab(changeorder: "ChangeOrder") -> bytes:
    """Generate professional Change Order PDF using ReportLab."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER,
                           leftMargin=0.6*inch, rightMargin=0.6*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=20,
        textColor=colors.HexColor('#1e3a5f'), alignment=TA_CENTER, spaceAfter=6
    )
    header_style = ParagraphStyle(
        'Header', parent=styles['Heading2'], fontSize=12,
        textColor=colors.HexColor('#1e3a5f'), spaceBefore=16, spaceAfter=8
    )
    normal_style = ParagraphStyle(
        'Normal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#374151')
    )
    small_style = ParagraphStyle(
        'Small', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748b')
    )
    
    elements = []
    
    # === LETTERHEAD ===
    letterhead_data = [
        [Paragraph(f"<b>{COMPANY_INFO['name'].upper()}</b>", 
                   ParagraphStyle('Company', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1e3a5f'))),
         Paragraph(f"{COMPANY_INFO['address']}<br/>{COMPANY_INFO['phone']}<br/>{COMPANY_INFO['email']}", small_style)]
    ]
    letterhead = Table(letterhead_data, colWidths=[4*inch, 3*inch])
    letterhead.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1e3a5f')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    elements.append(letterhead)
    elements.append(Spacer(1, 20))
    
    # === TITLE ===
    elements.append(Paragraph("<b>CHANGE ORDER</b>", title_style))
    elements.append(Paragraph(f"Document #CO-{changeorder.id:05d}", 
                              ParagraphStyle('Subtitle', parent=normal_style, alignment=TA_CENTER)))
    elements.append(Spacer(1, 16))
    
    # === STATUS BADGE ===
    status = changeorder.status.upper() if changeorder.status else "PENDING"
    status_color = colors.HexColor('#059669') if status == 'APPROVED' else colors.HexColor('#f59e0b')
    status_table = Table([[Paragraph(f"<b>{status}</b>", 
                          ParagraphStyle('Status', parent=normal_style, textColor=colors.white, alignment=TA_CENTER))]], 
                         colWidths=[1.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), status_color),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (0, 0), 6),
        ('BOTTOMPADDING', (0, 0), (0, 0), 6),
        ('LEFTPADDING', (0, 0), (0, 0), 12),
        ('RIGHTPADDING', (0, 0), (0, 0), 12),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 16))
    
    # === PROJECT & CO INFO ===
    project = changeorder.project
    pricing_type = "Fixed Price" if changeorder.pricing_type == "FIXED" else "Time & Materials"
    
    info_data = [
        [Paragraph("<b>PROJECT INFORMATION</b>", header_style), Paragraph("<b>CHANGE ORDER DETAILS</b>", header_style)],
        [Paragraph(f"<b>Project:</b> {project.name if project else '-'}", normal_style),
         Paragraph(f"<b>Date Created:</b> {changeorder.date_created.strftime('%B %d, %Y') if changeorder.date_created else '-'}", normal_style)],
        [Paragraph(f"<b>Project Code:</b> {project.project_code if project else '-'}", normal_style),
         Paragraph(f"<b>Pricing Type:</b> {pricing_type}", normal_style)],
        [Paragraph(f"<b>Client:</b> {project.client if project else '-'}", normal_style),
         Paragraph(f"<b>Amount:</b> <font color='#059669'><b>${changeorder.amount:,.2f}</b></font>", normal_style)],
    ]
    
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 16))
    
    # === SCOPE OF WORK ===
    elements.append(Paragraph("<b>SCOPE OF WORK</b>", header_style))
    desc_style = ParagraphStyle('Desc', parent=normal_style, leftIndent=10, borderColor=colors.HexColor('#1e3a5f'),
                                 borderWidth=0, borderPadding=8)
    description = changeorder.description or "No description provided."
    elements.append(Paragraph(description.replace('\n', '<br/>'), desc_style))
    elements.append(Spacer(1, 20))
    
    # === COST BREAKDOWN ===
    # Get expenses and time entries associated with this CO
    from decimal import Decimal as Dec
    from django.db.models import Sum
    
    material_expenses = changeorder.expenses.filter(category__in=["MATERIALES", "ALMACÉN"]).order_by("date")
    other_expenses = changeorder.expenses.exclude(category__in=["MATERIALES", "ALMACÉN", "MANO_OBRA"]).order_by("date")
    time_entries = changeorder.time_entries.select_related("employee").order_by("date")
    
    total_materials = material_expenses.aggregate(total=Sum("amount"))["total"] or Dec("0.00")
    total_other = other_expenses.aggregate(total=Sum("amount"))["total"] or Dec("0.00")
    total_labor_hours = sum((entry.hours_worked or Dec("0")) for entry in time_entries)
    labor_cost = sum(entry.labor_cost for entry in time_entries)
    
    # Get billing rate for display
    billing_rate = changeorder.get_effective_billing_rate() if hasattr(changeorder, "get_effective_billing_rate") else Dec("50.00")
    labor_billable = total_labor_hours * billing_rate
    
    # Only show cost breakdown section if there are expenses or time entries
    has_cost_data = material_expenses.exists() or other_expenses.exists() or time_entries.exists()
    
    if has_cost_data:
        elements.append(Paragraph("<b>COST BREAKDOWN</b>", header_style))
        
        # --- Materials Section ---
        if material_expenses.exists():
            elements.append(Paragraph("<b>Materials</b>", ParagraphStyle('SubHeader', parent=normal_style, fontSize=10, textColor=colors.HexColor('#059669'))))
            
            material_data = [
                [Paragraph("<b>Date</b>", small_style), 
                 Paragraph("<b>Description</b>", small_style), 
                 Paragraph("<b>Amount</b>", small_style)]
            ]
            for exp in material_expenses:
                material_data.append([
                    Paragraph(exp.date.strftime('%m/%d/%Y') if exp.date else '-', small_style),
                    Paragraph(str(exp.description or exp.category)[:50], small_style),
                    Paragraph(f"${exp.amount:,.2f}", small_style)
                ])
            # Add subtotal
            material_data.append([
                Paragraph("", small_style),
                Paragraph("<b>Materials Subtotal</b>", normal_style),
                Paragraph(f"<b>${total_materials:,.2f}</b>", normal_style)
            ])
            
            mat_table = Table(material_data, colWidths=[1*inch, 4.5*inch, 1.5*inch])
            mat_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
                ('LINEBELOW', (0, -2), (-1, -2), 1, colors.HexColor('#e2e8f0')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0fdf4')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(mat_table)
            elements.append(Spacer(1, 12))
        
        # --- Labor Section ---
        if time_entries.exists():
            elements.append(Paragraph("<b>Labor</b>", ParagraphStyle('SubHeader', parent=normal_style, fontSize=10, textColor=colors.HexColor('#3b82f6'))))
            
            labor_data = [
                [Paragraph("<b>Date</b>", small_style), 
                 Paragraph("<b>Employee</b>", small_style), 
                 Paragraph("<b>Hours</b>", small_style),
                 Paragraph("<b>Rate</b>", small_style),
                 Paragraph("<b>Amount</b>", small_style)]
            ]
            for entry in time_entries:
                emp_name = f"{entry.employee.first_name} {entry.employee.last_name}" if entry.employee else '-'
                hours = entry.hours_worked or Dec("0")
                rate = entry.billable_rate_snapshot or billing_rate
                amount = hours * rate
                labor_data.append([
                    Paragraph(entry.date.strftime('%m/%d/%Y') if entry.date else '-', small_style),
                    Paragraph(emp_name[:20], small_style),
                    Paragraph(f"{hours:.2f}", small_style),
                    Paragraph(f"${rate:,.2f}/hr", small_style),
                    Paragraph(f"${amount:,.2f}", small_style)
                ])
            # Add subtotal
            labor_data.append([
                Paragraph("", small_style),
                Paragraph("<b>Labor Subtotal</b>", normal_style),
                Paragraph(f"<b>{total_labor_hours:.2f} hrs</b>", normal_style),
                Paragraph("", small_style),
                Paragraph(f"<b>${labor_billable:,.2f}</b>", normal_style)
            ])
            
            labor_table = Table(labor_data, colWidths=[0.9*inch, 2.1*inch, 0.9*inch, 1.2*inch, 1.2*inch])
            labor_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
                ('LINEBELOW', (0, -2), (-1, -2), 1, colors.HexColor('#e2e8f0')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eff6ff')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(labor_table)
            elements.append(Spacer(1, 12))
        
        # --- Other Expenses Section ---
        if other_expenses.exists():
            elements.append(Paragraph("<b>Other Expenses</b>", ParagraphStyle('SubHeader', parent=normal_style, fontSize=10, textColor=colors.HexColor('#f59e0b'))))
            
            other_data = [
                [Paragraph("<b>Date</b>", small_style), 
                 Paragraph("<b>Category</b>", small_style),
                 Paragraph("<b>Description</b>", small_style), 
                 Paragraph("<b>Amount</b>", small_style)]
            ]
            for exp in other_expenses:
                other_data.append([
                    Paragraph(exp.date.strftime('%m/%d/%Y') if exp.date else '-', small_style),
                    Paragraph(str(exp.category)[:15], small_style),
                    Paragraph(str(exp.description or '-')[:40], small_style),
                    Paragraph(f"${exp.amount:,.2f}", small_style)
                ])
            # Add subtotal
            other_data.append([
                Paragraph("", small_style),
                Paragraph("", small_style),
                Paragraph("<b>Other Subtotal</b>", normal_style),
                Paragraph(f"<b>${total_other:,.2f}</b>", normal_style)
            ])
            
            other_table = Table(other_data, colWidths=[1*inch, 1.2*inch, 3.3*inch, 1.5*inch])
            other_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
                ('LINEBELOW', (0, -2), (-1, -2), 1, colors.HexColor('#e2e8f0')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fffbeb')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(other_table)
            elements.append(Spacer(1, 12))
        
        # --- Grand Total ---
        grand_total = total_materials + labor_billable + total_other
        
        # For FIXED pricing, show the fixed amount instead
        if changeorder.pricing_type == "FIXED":
            display_total = changeorder.amount
        else:
            display_total = grand_total
        
        total_data = [
            [Paragraph("<b>TOTAL</b>", ParagraphStyle('TotalLabel', parent=normal_style, fontSize=12, textColor=colors.HexColor('#1e3a5f'))),
             Paragraph(f"<b>${display_total:,.2f}</b>", ParagraphStyle('TotalValue', parent=normal_style, fontSize=14, textColor=colors.HexColor('#059669')))]
        ]
        total_table = Table(total_data, colWidths=[5.5*inch, 1.5*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#059669')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 20))
    
    # === TERMS & CONDITIONS ===
    elements.append(Paragraph("<b>TERMS & CONDITIONS</b>", header_style))
    terms = [
        "1. This Change Order becomes effective upon signature by both parties.",
        "2. Work described herein is in addition to the original contract scope.",
        "3. Payment terms follow the original contract unless otherwise specified.",
        "4. Any additional changes require a new Change Order.",
        "5. This Change Order is subject to the terms of the original contract agreement."
    ]
    for term in terms:
        elements.append(Paragraph(term, small_style))
    elements.append(Spacer(1, 24))
    
    # === SIGNATURES ===
    elements.append(Paragraph("<b>AUTHORIZATION & SIGNATURES</b>", header_style))
    
    # --- Client Signature ---
    client_sig_content = []
    client_sig_content.append(Paragraph("<b>CLIENT SIGNATURE</b>", small_style))
    
    # Try to load client signature image
    client_sig_img = None
    if changeorder.signature_image:
        try:
            sig_file = changeorder.signature_image
            if hasattr(sig_file, 'open'):
                with sig_file.open('rb') as f:
                    sig_bytes = f.read()
            else:
                sig_file.seek(0)
                sig_bytes = sig_file.read()
            sig_buffer = BytesIO(sig_bytes)
            client_sig_img = Image(sig_buffer, width=2.5*inch, height=0.8*inch)
        except Exception:
            client_sig_img = None
    
    if client_sig_img:
        client_sig_content.append(Spacer(1, 8))
        client_sig_content.append(client_sig_img)
    else:
        client_sig_content.append(Paragraph("<br/><br/>_________________________", normal_style))
    
    signed_by = changeorder.signed_by or "_________________________"
    signed_date = changeorder.signed_at.strftime('%B %d, %Y') if changeorder.signed_at else "_______________"
    client_sig_content.append(Paragraph(f"{signed_by}", normal_style))
    client_sig_content.append(Paragraph(f"Date: {signed_date}", small_style))
    
    # --- Contractor Signature ---
    contractor_sig_content = []
    contractor_sig_content.append(Paragraph("<b>CONTRACTOR SIGNATURE</b>", small_style))
    
    # Try to load contractor signature image
    contractor_sig_img = None
    if hasattr(changeorder, 'contractor_signature') and changeorder.contractor_signature:
        try:
            sig_file = changeorder.contractor_signature
            if hasattr(sig_file, 'open'):
                with sig_file.open('rb') as f:
                    sig_bytes = f.read()
            else:
                sig_file.seek(0)
                sig_bytes = sig_file.read()
            sig_buffer = BytesIO(sig_bytes)
            contractor_sig_img = Image(sig_buffer, width=2.5*inch, height=0.8*inch)
        except Exception:
            contractor_sig_img = None
    
    if contractor_sig_img:
        contractor_sig_content.append(Spacer(1, 8))
        contractor_sig_content.append(contractor_sig_img)
    else:
        contractor_sig_content.append(Paragraph("<br/><br/>_________________________", normal_style))
    
    contractor_signed_by = getattr(changeorder, 'contractor_signed_by', '') or COMPANY_INFO['name']
    contractor_signed_date = ""
    if hasattr(changeorder, 'contractor_signed_at') and changeorder.contractor_signed_at:
        contractor_signed_date = changeorder.contractor_signed_at.strftime('%B %d, %Y')
    else:
        contractor_signed_date = "_______________"
    contractor_sig_content.append(Paragraph(f"{contractor_signed_by}", normal_style))
    contractor_sig_content.append(Paragraph(f"Date: {contractor_signed_date}", small_style))
    
    # Build signature table
    sig_data = [
        [client_sig_content, contractor_sig_content],
    ]
    
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#d1d5db')),
        ('BOX', (1, 0), (1, -1), 1, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 24))
    
    # === FOOTER ===
    hash_data = {"id": changeorder.id, "amount": str(changeorder.amount), "project": project.name if project else ""}
    doc_hash = _generate_document_hash(hash_data)
    
    footer_text = f"Document Hash: {doc_hash} | Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if changeorder.signed_ip:
        footer_text += f" | Signing IP: {changeorder.signed_ip}"
    
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER)))
    elements.append(Paragraph(f"<i>This document was electronically generated by {COMPANY_INFO['name']}.</i>", 
                              ParagraphStyle('FooterNote', parent=small_style, alignment=TA_CENTER)))
    
    doc.build(elements)
    return buffer.getvalue()


def generate_colorsample_pdf_reportlab(colorsample: "ColorSample") -> bytes:
    """Generate professional Color Sample Approval PDF using ReportLab with images."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER,
                           leftMargin=0.6*inch, rightMargin=0.6*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles with purple theme
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=20,
        textColor=colors.HexColor('#7c3aed'), alignment=TA_CENTER, spaceAfter=6
    )
    header_style = ParagraphStyle(
        'Header', parent=styles['Heading2'], fontSize=12,
        textColor=colors.HexColor('#7c3aed'), spaceBefore=16, spaceAfter=8
    )
    normal_style = ParagraphStyle(
        'Normal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#374151')
    )
    small_style = ParagraphStyle(
        'Small', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748b')
    )
    center_style = ParagraphStyle(
        'Center', parent=normal_style, alignment=TA_CENTER
    )
    
    elements = []
    
    # === LETTERHEAD ===
    letterhead_data = [
        [Paragraph(f"<b>{COMPANY_INFO['name'].upper()}</b>", 
                   ParagraphStyle('Company', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#7c3aed'))),
         Paragraph(f"{COMPANY_INFO['address']}<br/>{COMPANY_INFO['phone']}<br/>{COMPANY_INFO['email']}", small_style)]
    ]
    letterhead = Table(letterhead_data, colWidths=[4*inch, 3*inch])
    letterhead.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#7c3aed')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    elements.append(letterhead)
    elements.append(Spacer(1, 16))
    
    # === TITLE ===
    elements.append(Paragraph("<b>COLOR SAMPLE APPROVAL</b>", title_style))
    sample_num = colorsample.sample_number or colorsample.id
    elements.append(Paragraph(f"Sample #{sample_num} | Version {getattr(colorsample, 'version', 1)}", 
                              ParagraphStyle('Subtitle', parent=normal_style, alignment=TA_CENTER)))
    elements.append(Spacer(1, 12))
    
    # === STATUS BADGE ===
    status = colorsample.status.upper() if colorsample.status else "PENDING"
    status_color = colors.HexColor('#059669') if status == 'APPROVED' else colors.HexColor('#f59e0b')
    status_table = Table([[Paragraph(f"<b>✓ {status}</b>", 
                          ParagraphStyle('Status', parent=normal_style, textColor=colors.white, alignment=TA_CENTER))]], 
                         colWidths=[1.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), status_color),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (0, 0), 6),
        ('BOTTOMPADDING', (0, 0), (0, 0), 6),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 16))
    
    # === SAMPLE IMAGES (CENTER OF DOCUMENT - PROFESSIONAL TABLE LAYOUT) ===
    elements.append(Paragraph("<b>COLOR SAMPLE IMAGES</b>", header_style))
    
    has_sample = bool(colorsample.sample_image)
    has_reference = bool(colorsample.reference_photo)
    
    sample_img = None
    ref_img = None
    
    # Load Sample Image
    if has_sample:
        try:
            # Handle both local and remote storage (S3, etc.)
            img_file = colorsample.sample_image
            if hasattr(img_file, 'open'):
                with img_file.open('rb') as f:
                    img_bytes = f.read()
            else:
                img_file.seek(0)
                img_bytes = img_file.read()
            img_buffer = BytesIO(img_bytes)
            sample_img = Image(img_buffer, width=2.6*inch, height=2.6*inch)
        except Exception:
            sample_img = None
    
    # Load Reference Photo
    if has_reference:
        try:
            # Handle both local and remote storage (S3, etc.)
            ref_file = colorsample.reference_photo
            if hasattr(ref_file, 'open'):
                with ref_file.open('rb') as f:
                    ref_bytes = f.read()
            else:
                ref_file.seek(0)
                ref_bytes = ref_file.read()
            ref_buffer = BytesIO(ref_bytes)
            ref_img = Image(ref_buffer, width=2.6*inch, height=2.6*inch)
        except Exception:
            ref_img = None
    
    # Build professional image table with subtle borders
    if sample_img or ref_img:
        if sample_img and ref_img:
            # Two images side by side in elegant table
            img_data = [
                [Paragraph("<b>Sample Image</b>", center_style), 
                 Paragraph("<b>Reference Photo</b>", center_style)],
                [sample_img, ref_img]
            ]
            img_table = Table(img_data, colWidths=[3.3*inch, 3.3*inch])
            img_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#faf5ff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Subtle outer border (purple accent)
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#c4b5fd')),
                # Inner vertical line separating images
                ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.HexColor('#e9d5ff')),
                # Horizontal line under header
                ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#e9d5ff')),
                # Padding
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 1), (-1, 1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                # Background for image cells
                ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ]))
        elif sample_img:
            # Single sample image centered
            img_data = [
                [Paragraph("<b>Sample Image</b>", center_style)],
                [sample_img]
            ]
            img_table = Table(img_data, colWidths=[3.5*inch])
            img_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#faf5ff')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#c4b5fd')),
                ('LINEBELOW', (0, 0), (0, 0), 0.5, colors.HexColor('#e9d5ff')),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('TOPPADDING', (0, 1), (0, 1), 12),
                ('BOTTOMPADDING', (0, 1), (0, 1), 12),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
            ]))
        else:
            # Only reference photo
            img_data = [
                [Paragraph("<b>Reference Photo</b>", center_style)],
                [ref_img]
            ]
            img_table = Table(img_data, colWidths=[3.5*inch])
            img_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#faf5ff')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#c4b5fd')),
                ('LINEBELOW', (0, 0), (0, 0), 0.5, colors.HexColor('#e9d5ff')),
                ('TOPPADDING', (0, 0), (0, 0), 8),
                ('BOTTOMPADDING', (0, 0), (0, 0), 8),
                ('TOPPADDING', (0, 1), (0, 1), 12),
                ('BOTTOMPADDING', (0, 1), (0, 1), 12),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
            ]))
        
        # Wrap table in a centered container
        container = Table([[img_table]], colWidths=[7*inch])
        container.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        elements.append(container)
    else:
        # No images placeholder
        no_img_table = Table([
            [Paragraph("<i>No sample images available</i>", center_style)]
        ], colWidths=[6*inch])
        no_img_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f9fafb')),
            ('TOPPADDING', (0, 0), (0, 0), 20),
            ('BOTTOMPADDING', (0, 0), (0, 0), 20),
        ]))
        elements.append(no_img_table)
    
    elements.append(Spacer(1, 16))
    
    # === COLOR INFORMATION ===
    elements.append(Paragraph("<b>COLOR DETAILS</b>", header_style))
    
    color_data = [
        [Paragraph("<b>Color Code</b>", small_style), Paragraph("<b>Color Name</b>", small_style), 
         Paragraph("<b>Brand</b>", small_style), Paragraph("<b>Finish</b>", small_style)],
        [Paragraph(f"<font size='14'><b>{colorsample.code or '-'}</b></font>", normal_style),
         Paragraph(f"{colorsample.name or '-'}", normal_style),
         Paragraph(f"{colorsample.brand or '-'}", normal_style),
         Paragraph(f"{colorsample.finish or '-'}", normal_style)],
    ]
    
    color_table = Table(color_data, colWidths=[1.8*inch, 2*inch, 1.7*inch, 1.5*inch])
    color_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#faf5ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9d5ff')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(color_table)
    elements.append(Spacer(1, 12))
    
    # === PROJECT & LOCATION ===
    project = colorsample.project
    elements.append(Paragraph("<b>PROJECT & LOCATION</b>", header_style))
    
    project_data = [
        [Paragraph(f"<b>Project:</b> {project.name if project else '-'}", normal_style),
         Paragraph(f"<b>Project Code:</b> {project.project_code if project else '-'}", normal_style)],
        [Paragraph(f"<b>Application Location:</b> {colorsample.room_location or 'Not specified'}", normal_style),
         Paragraph(f"<b>Room Group:</b> {getattr(colorsample, 'room_group', '-') or '-'}", normal_style)],
    ]
    
    project_table = Table(project_data, colWidths=[3.5*inch, 3.5*inch])
    project_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(project_table)
    elements.append(Spacer(1, 12))
    
    # === CLIENT APPROVAL SECTION WITH SIGNATURE ===
    elements.append(Paragraph("<b>CLIENT APPROVAL</b>", header_style))
    
    signed_name = colorsample.client_signed_name or "_________________________"
    signed_date = colorsample.client_signed_at.strftime('%B %d, %Y at %I:%M %p') if colorsample.client_signed_at else "_______________"
    
    # Approval info
    approval_data = [
        [Paragraph("<b>Approved By:</b>", small_style), Paragraph(f"{signed_name}", normal_style)],
        [Paragraph("<b>Approval Date:</b>", small_style), Paragraph(f"{signed_date}", normal_style)],
    ]
    
    approval_table = Table(approval_data, colWidths=[1.5*inch, 5.5*inch])
    approval_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#059669')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(approval_table)
    elements.append(Spacer(1, 12))
    
    # Client Signature Image
    if colorsample.client_signature:
        try:
            # Handle both local and remote storage (S3, etc.)
            sig_file = colorsample.client_signature
            if hasattr(sig_file, 'open'):
                with sig_file.open('rb') as f:
                    sig_bytes = f.read()
            else:
                sig_file.seek(0)
                sig_bytes = sig_file.read()
            sig_buffer = BytesIO(sig_bytes)
            sig_image = Image(sig_buffer, width=2.5*inch, height=0.8*inch)
            
            sig_table = Table([
                [Paragraph("<b>Client Signature:</b>", small_style)],
                [sig_image],
            ], colWidths=[3*inch])
            sig_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BOX', (0, 1), (0, 1), 1, colors.HexColor('#059669')),
                ('BACKGROUND', (0, 1), (0, 1), colors.white),
            ]))
            elements.append(sig_table)
        except Exception:
            elements.append(Paragraph("<i>[Digital signature on file]</i>", small_style))
    else:
        elements.append(Paragraph("<i>[Signature pending]</i>", small_style))
    
    elements.append(Spacer(1, 16))
    
    # === IMPORTANT NOTICE ===
    notice_style = ParagraphStyle('Notice', parent=small_style, backColor=colors.HexColor('#fef3c7'),
                                   borderColor=colors.HexColor('#fbbf24'), borderWidth=1, borderPadding=8)
    elements.append(Paragraph(
        "<b>Important:</b> Color appearance may vary based on lighting conditions, surface texture, and surrounding colors. "
        "A small test application is recommended before full application. Final color should be verified in natural daylight.",
        notice_style
    ))
    elements.append(Spacer(1, 16))
    
    # === FOOTER ===
    hash_data = {"id": colorsample.id, "code": colorsample.code, "project": project.name if project else ""}
    doc_hash = _generate_document_hash(hash_data)
    
    footer_text = f"Document Hash: {doc_hash} | Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if colorsample.approval_ip:
        footer_text += f" | Signing IP: {colorsample.approval_ip}"
    
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER)))
    elements.append(Paragraph(f"<i>This document was electronically generated by {COMPANY_INFO['name']}.</i>", 
                              ParagraphStyle('FooterNote', parent=small_style, alignment=TA_CENTER)))
    
    doc.build(elements)
    return buffer.getvalue()


# Convenience functions
def generate_signed_changeorder_pdf(changeorder: "ChangeOrder") -> bytes:
    """Generate PDF for signed Change Order."""
    if HAS_REPORTLAB:
        return generate_changeorder_pdf_reportlab(changeorder)
    return PDFDocumentGenerator.generate_changeorder_pdf(changeorder)


def generate_signed_colorsample_pdf(colorsample: "ColorSample") -> bytes:
    """Generate PDF for signed Color Sample."""
    if HAS_REPORTLAB:
        return generate_colorsample_pdf_reportlab(colorsample)
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
