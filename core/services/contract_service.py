"""
Contract Service - Auto-generate contracts from approved estimates

This service handles the complete contract workflow:
1. Generate Contract when estimate is approved
2. Generate Contract PDF with legal terms
3. Handle client signature capture
4. Generate signed contract PDF
5. Handle revision requests

Workflow:
    Estimate Approved 
    → Contract Created (status='pending_signature')
    → PDF Generated & Sent to Client
    → Client Signs → Signed PDF → status='signed' → Project Activated
    OR
    → Client Requests Changes → status='revision_requested' → Admin Edits
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Optional, Dict, Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from core.models import Contract, Estimate, Project, ProjectFile

logger = logging.getLogger(__name__)


# Company information for contracts
COMPANY_INFO = {
    "name": "Kibray Paint & Stain LLC",
    "address": "P.O. Box 25881, Silverthorne, CO 80497",
    "phone": "(970) 333-4872",
    "email": "jduran@kibraypainting.net",
    "website": "kibraypainting.net",
    "license": "Licensed & Insured",
}


class ContractService:
    """Service for managing contract generation and workflow."""
    
    @staticmethod
    @transaction.atomic
    def create_contract_from_estimate(
        estimate: "Estimate",
        user: Optional["User"] = None,
        auto_generate_pdf: bool = True
    ) -> "Contract":
        """
        Create a Contract from an approved Estimate.
        
        Args:
            estimate: The approved estimate
            user: User creating the contract (for audit)
            auto_generate_pdf: Whether to auto-generate PDF
            
        Returns:
            Created Contract instance
            
        Raises:
            ValueError: If estimate is not approved or already has a contract
        """
        from core.models import Contract
        
        # Validation
        if not estimate.approved:
            raise ValueError("Cannot create contract from unapproved estimate")
        
        if hasattr(estimate, 'contract') and estimate.contract:
            raise ValueError(f"Estimate {estimate.code} already has a contract")
        
        # Create contract
        contract = Contract(
            estimate=estimate,
            project=estimate.project,
            status='pending_signature',
        )
        
        # Save will auto-generate:
        # - contract_number (from estimate.code + "-C")
        # - client_view_token (UUID)
        # - total_amount (from estimate calculation)
        # - payment_schedule (default 33/33/34)
        contract.save()
        
        logger.info(f"Created contract {contract.contract_number} from estimate {estimate.code}")
        
        # Generate PDF if requested
        if auto_generate_pdf:
            try:
                pdf_file = ContractService.generate_contract_pdf(contract, user)
                if pdf_file:
                    contract.pdf_file = pdf_file
                    contract.save(update_fields=['pdf_file'])
                    logger.info(f"Generated PDF for contract {contract.contract_number}")
            except Exception as e:
                logger.error(f"Failed to generate PDF for contract {contract.contract_number}: {e}")
        
        return contract
    
    @staticmethod
    def generate_contract_pdf(
        contract: "Contract",
        user: Optional["User"] = None
    ) -> Optional["ProjectFile"]:
        """
        Generate Contract PDF and save to project files.
        
        Args:
            contract: Contract instance
            user: User generating the PDF
            
        Returns:
            ProjectFile instance or None if failed
        """
        from core.services.document_storage_service import save_pdf_to_project_files
        from core.services.pdf_service import generate_contract_pdf_reportlab
        
        try:
            # Generate PDF bytes
            pdf_bytes = generate_contract_pdf_reportlab(contract)
            
            # Build filename
            filename = f"Contract_{contract.contract_number}.pdf"
            filename = filename.replace("/", "-").replace("\\", "-").replace(" ", "_")
            
            # Save to project files
            project_file = save_pdf_to_project_files(
                project=contract.project,
                pdf_bytes=pdf_bytes,
                filename=filename,
                document_type="contract",
                user=user,
                source_record=contract.estimate,
                overwrite=True,
            )
            
            return project_file
            
        except Exception as e:
            logger.error(f"Failed to generate contract PDF: {e}")
            return None
    
    @staticmethod
    @transaction.atomic
    def sign_contract(
        contract: "Contract",
        client_name: str,
        signature_data: Optional[bytes] = None,
        ip_address: Optional[str] = None,
        generate_signed_pdf: bool = True,
        user: Optional["User"] = None
    ) -> "Contract":
        """
        Process client signature on contract.
        
        Args:
            contract: Contract to sign
            client_name: Client's typed name
            signature_data: Base64 decoded signature image bytes
            ip_address: Client's IP address
            generate_signed_pdf: Whether to generate signed PDF
            user: Staff user (for countersign)
            
        Returns:
            Updated Contract instance
            
        Raises:
            ValueError: If contract cannot be signed
        """
        from core.models import Contract
        
        if not contract.can_be_signed:
            raise ValueError(f"Contract {contract.contract_number} cannot be signed (status: {contract.status})")
        
        # Save signature
        contract.client_signed_name = client_name
        contract.client_signed_at = timezone.now()
        contract.client_ip_address = ip_address
        
        if signature_data:
            # Save signature image
            filename = f"signature_{contract.contract_number}_{timezone.now().strftime('%Y%m%d%H%M%S')}.png"
            contract.client_signature.save(filename, ContentFile(signature_data), save=False)
        
        # Update status
        contract.status = 'signed'
        
        # Auto-countersign by staff if provided
        if user and user.is_staff:
            contract.contractor_signed_at = timezone.now()
            contract.contractor_signed_by = user
            contract.status = 'active'
        
        contract.save()
        
        logger.info(f"Contract {contract.contract_number} signed by {client_name}")
        
        # Generate signed PDF
        if generate_signed_pdf:
            try:
                signed_pdf = ContractService.generate_signed_contract_pdf(contract, user)
                if signed_pdf:
                    contract.signed_pdf_file = signed_pdf
                    contract.save(update_fields=['signed_pdf_file'])
            except Exception as e:
                logger.error(f"Failed to generate signed PDF: {e}")
        
        return contract
    
    @staticmethod
    def generate_signed_contract_pdf(
        contract: "Contract",
        user: Optional["User"] = None
    ) -> Optional["ProjectFile"]:
        """
        Generate signed Contract PDF with signature embedded.
        
        Args:
            contract: Signed contract instance
            user: User generating the PDF
            
        Returns:
            ProjectFile instance or None if failed
        """
        from core.services.document_storage_service import save_pdf_to_project_files
        from core.services.pdf_service import generate_signed_contract_pdf_reportlab
        
        try:
            # Generate PDF bytes with signature
            pdf_bytes = generate_signed_contract_pdf_reportlab(contract)
            
            # Build filename
            filename = f"Contract_{contract.contract_number}_SIGNED.pdf"
            filename = filename.replace("/", "-").replace("\\", "-").replace(" ", "_")
            
            # Save to project files
            project_file = save_pdf_to_project_files(
                project=contract.project,
                pdf_bytes=pdf_bytes,
                filename=filename,
                document_type="signed_contract",
                user=user,
                source_record=contract.estimate,
                overwrite=True,
            )
            
            return project_file
            
        except Exception as e:
            logger.error(f"Failed to generate signed contract PDF: {e}")
            return None
    
    @staticmethod
    @transaction.atomic
    def request_revision(
        contract: "Contract",
        revision_notes: str,
    ) -> "Contract":
        """
        Handle client request for contract revision.
        
        Args:
            contract: Contract to revise
            revision_notes: Client's notes about needed changes
            
        Returns:
            Updated Contract instance
        """
        if contract.status not in ['pending_signature', 'revision_requested']:
            raise ValueError(f"Contract {contract.contract_number} cannot be revised (status: {contract.status})")
        
        contract.status = 'revision_requested'
        contract.revision_notes = revision_notes
        contract.revision_requested_at = timezone.now()
        contract.revision_count += 1
        contract.save()
        
        logger.info(f"Revision requested for contract {contract.contract_number}")
        
        # TODO: Send notification to admin
        # NotificationService.notify_contract_revision(contract)
        
        return contract
    
    @staticmethod
    @transaction.atomic
    def update_contract_from_estimate(
        contract: "Contract",
        user: Optional["User"] = None
    ) -> "Contract":
        """
        Update contract after estimate has been revised.
        
        Args:
            contract: Contract to update
            user: User making the update
            
        Returns:
            Updated Contract instance
        """
        if contract.status != 'revision_requested':
            raise ValueError("Contract must be in revision_requested status to update")
        
        # Recalculate totals from estimate
        contract.total_amount = contract.calculate_total_from_estimate()
        contract.payment_schedule = contract.generate_default_payment_schedule()
        
        # Increment version
        contract.version += 1
        
        # Reset to pending signature
        contract.status = 'pending_signature'
        contract.revision_notes = ""
        
        contract.save()
        
        # Regenerate PDF
        try:
            pdf_file = ContractService.generate_contract_pdf(contract, user)
            if pdf_file:
                contract.pdf_file = pdf_file
                contract.save(update_fields=['pdf_file'])
        except Exception as e:
            logger.error(f"Failed to regenerate PDF for updated contract: {e}")
        
        logger.info(f"Contract {contract.contract_number} updated to v{contract.version}")
        
        return contract
    
    @staticmethod
    def get_contract_by_token(token: str) -> Optional["Contract"]:
        """
        Get contract by client view token.
        
        Args:
            token: Client view token (UUID)
            
        Returns:
            Contract instance or None
        """
        from core.models import Contract
        
        try:
            return Contract.objects.select_related(
                'estimate',
                'project',
                'pdf_file',
                'signed_pdf_file'
            ).get(client_view_token=token)
        except Contract.DoesNotExist:
            return None
    
    @staticmethod
    def get_contract_context(contract: "Contract") -> Dict[str, Any]:
        """
        Get full context for contract template/PDF generation.
        
        Args:
            contract: Contract instance
            
        Returns:
            Dictionary with all contract data
        """
        estimate = contract.estimate
        project = contract.project
        
        # Get line items
        lines = estimate.lines.select_related('cost_code').all()
        
        # Calculate totals
        subtotal = sum(line.direct_cost() for line in lines)
        
        # Get component totals
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
        
        # Calculate markups
        labor_markup = total_labor * (estimate.markup_labor / 100) if estimate.markup_labor else Decimal("0")
        material_markup = total_material * (estimate.markup_material / 100) if estimate.markup_material else Decimal("0")
        overhead = subtotal * (estimate.overhead_pct / 100) if estimate.overhead_pct else Decimal("0")
        profit = subtotal * (estimate.target_profit_pct / 100) if estimate.target_profit_pct else Decimal("0")
        
        return {
            'contract': contract,
            'estimate': estimate,
            'project': project,
            'company': COMPANY_INFO,
            'lines': lines,
            'subtotal': subtotal,
            'labor_markup': labor_markup,
            'material_markup': material_markup,
            'overhead': overhead,
            'profit': profit,
            'grand_total': contract.total_amount,
            'payment_schedule': contract.payment_schedule,
            'is_signed': contract.is_signed,
            'can_be_signed': contract.can_be_signed,
            'generation_date': timezone.now(),
        }


# Convenience functions for direct import
def create_contract_from_estimate(estimate, user=None, auto_generate_pdf=True):
    """Create contract from approved estimate."""
    return ContractService.create_contract_from_estimate(estimate, user, auto_generate_pdf)


def sign_contract(contract, client_name, signature_data=None, ip_address=None, generate_signed_pdf=True, user=None):
    """Process client signature on contract."""
    return ContractService.sign_contract(contract, client_name, signature_data, ip_address, generate_signed_pdf, user)


def request_contract_revision(contract, revision_notes):
    """Handle client request for contract revision."""
    return ContractService.request_revision(contract, revision_notes)


def get_contract_by_token(token):
    """Get contract by client view token."""
    return ContractService.get_contract_by_token(token)
