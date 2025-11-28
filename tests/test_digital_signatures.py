"""
Tests for Digital Signature System (Gap A Implementation)
Tests cryptographic signature creation, verification, and tamper detection.
"""
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import ChangeOrder, ColorSample, DigitalSignature, Project
from core.signature_utils import (
    bulk_verify_signatures,
    create_signature,
    export_signature_proof,
    verify_signature,
)


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def project(db):
    """Create test project"""
    return Project.objects.create(
        name='Test Project',
        project_code='PRJ-0001',
        start_date=timezone.now().date()
    )


@pytest.fixture
def color_sample(db, project, user):
    """Create test color sample"""
    return ColorSample.objects.create(
        project=project,
        code='SW 7008',
        name='Alabaster',
        brand='Sherwin Williams',
        status='proposed',
        created_by=user
    )


@pytest.fixture
def change_order(db, project):
    """Create test change order"""
    return ChangeOrder.objects.create(
        project=project,
        description='Test Change Order',
        amount=Decimal('1500.00'),
        status='draft'
    )


@pytest.mark.django_db
class TestDigitalSignatureCreation:
    """Test digital signature creation"""
    
    def test_create_signature_for_color_sample(self, color_sample, user):
        """Test creating digital signature for color sample"""
        signature = create_signature(
            entity=color_sample,
            signer=user,
            ip_address='192.168.1.100',
            signature_canvas_data='data:image/png;base64,iVBORw0KG...',
            user_agent='Mozilla/5.0',
            geolocation={'lat': 40.7128, 'lng': -74.0060}
        )
        
        assert signature is not None
        assert signature.entity_type == 'color_sample'
        assert signature.entity_id == color_sample.id
        assert signature.signer == user
        assert signature.ip_address == '192.168.1.100'
        assert signature.signed_hash is not None
        assert len(signature.signed_hash) == 64  # SHA256 produces 64 hex chars
        assert signature.document_snapshot is not None
        assert signature.verification_count == 0
    
    def test_create_signature_for_change_order(self, change_order, user):
        """Test creating digital signature for change order"""
        signature = create_signature(
            entity=change_order,
            signer=user,
            ip_address='10.0.0.50'
        )
        
        assert signature is not None
        assert signature.entity_type == 'change_order'
        assert signature.entity_id == change_order.id
        assert signature.signer == user
        assert signature.signed_hash is not None
    
    def test_signature_auto_computes_hash_on_save(self, color_sample, user):
        """Test that signature hash is auto-computed on save"""
        from signatures.models import Signature as BaseSignature
        
        snapshot = color_sample.get_signature_snapshot()
        
        # Create base signature first
        base_sig = BaseSignature.objects.create(
            signer=user,
            title=f"Test Signature for ColorSample #{color_sample.id}",
            hash_alg='sha256',
            content_hash='test_hash',
            note='Test signature'
        )
        
        signature = DigitalSignature(
            base_signature=base_sig,
            entity_type='color_sample',
            entity_id=color_sample.id,
            signer=user,
            signature_data='test_data',
            document_snapshot=snapshot
        )
        
        # Hash should be None before save
        assert signature.signed_hash is None or signature.signed_hash == ''
        
        signature.save()
        
        # Hash should be computed after save
        assert signature.signed_hash is not None
        assert len(signature.signed_hash) == 64


@pytest.mark.django_db
class TestSignatureVerification:
    """Test signature verification and tamper detection"""
    
    def test_verify_valid_signature(self, color_sample, user):
        """Test verification of unmodified signature"""
        # Create signature
        signature = create_signature(
            entity=color_sample,
            signer=user,
            ip_address='192.168.1.1'
        )
        
        # Associate signature with entity
        color_sample.digital_signature = signature
        color_sample.save()
        
        # Verify signature
        is_valid, message = verify_signature(color_sample)
        
        assert is_valid is True
        assert 'no tampering detected' in message.lower()
        
        # Check verification was tracked
        signature.refresh_from_db()
        assert signature.verification_count == 1
        assert signature.verified_at is not None
    
    def test_detect_tampered_signature(self, color_sample, user):
        """Test detection of tampered document"""
        # Create signature
        signature = create_signature(
            entity=color_sample,
            signer=user,
            ip_address='192.168.1.1'
        )
        
        # Associate signature with entity
        color_sample.digital_signature = signature
        color_sample.save()
        
        # Tamper with document snapshot
        signature.document_snapshot['code'] = 'TAMPERED'
        signature.save(update_fields=['document_snapshot'])
        
        # Verify signature - should detect tampering
        is_valid, message = verify_signature(color_sample)
        
        assert is_valid is False
        assert 'tamper detected' in message.lower()
        assert 'hash mismatch' in message.lower()
    
    def test_verify_signature_without_digital_signature(self, color_sample):
        """Test verification fails gracefully when no signature exists"""
        is_valid, message = verify_signature(color_sample)
        
        assert is_valid is False
        assert 'no digital signature' in message.lower()
    
    def test_verification_increments_count(self, color_sample, user):
        """Test that verification count increments properly"""
        signature = create_signature(
            entity=color_sample,
            signer=user
        )
        color_sample.digital_signature = signature
        color_sample.save()
        
        # Verify multiple times
        for i in range(3):
            verify_signature(color_sample)
            signature.refresh_from_db()
            assert signature.verification_count == i + 1


@pytest.mark.django_db
class TestBulkVerification:
    """Test bulk signature verification"""
    
    def test_bulk_verify_mixed_results(self, project, user):
        """Test bulk verification with mixed valid/invalid signatures"""
        # Create 3 color samples with signatures
        samples = []
        for i in range(3):
            sample = ColorSample.objects.create(
                project=project,
                code=f'SW {i}',
                name=f'Color {i}',
                status='proposed',
                created_by=user
            )
            signature = create_signature(
                entity=sample,
                signer=user
            )
            sample.digital_signature = signature
            sample.save()
            samples.append(sample)
        
        # Tamper with one signature
        samples[1].digital_signature.document_snapshot['name'] = 'TAMPERED'
        samples[1].digital_signature.save()
        
        # Bulk verify
        queryset = ColorSample.objects.filter(id__in=[s.id for s in samples])
        results = bulk_verify_signatures(queryset)
        
        assert results['total'] == 3
        assert results['valid'] == 2
        assert results['invalid'] == 1
        assert len(results['details']) == 3
        assert results['details'][0]['is_valid'] is True
        assert results['details'][1]['is_valid'] is False
        assert results['details'][2]['is_valid'] is True
        assert 'tamper detected' in results['details'][1]['message'].lower()
    
    def test_bulk_verify_empty_queryset(self):
        """Test bulk verification with empty queryset"""
        queryset = ColorSample.objects.none()
        results = bulk_verify_signatures(queryset)
        
        assert results['total'] == 0
        assert results['valid'] == 0
        assert results['invalid'] == 0
        assert results['unsigned'] == 0
        assert results['details'] == []


@pytest.mark.django_db
class TestSignatureExport:
    """Test signature proof export"""
    
    def test_export_signature_proof_json(self, color_sample, user):
        """Test exporting signature proof as JSON"""
        signature = create_signature(
            entity=color_sample,
            signer=user,
            ip_address='192.168.1.1',
            signature_canvas_data='test_data',
            user_agent='Mozilla/5.0',
            geolocation={'lat': 40.7128, 'lng': -74.0060}
        )
        color_sample.digital_signature = signature
        color_sample.save()
        
        proof = export_signature_proof(color_sample, format='json')
        
        assert proof is not None
        assert isinstance(proof, str)
        
        # Parse JSON to verify structure
        data = json.loads(proof)
        assert 'entity_type' in data
        assert 'entity_id' in data
        assert 'signer' in data
        assert 'timestamp' in data
        assert 'signed_hash' in data
        assert 'document_snapshot' in data
        assert 'verification_status' in data
        assert data['entity_type'] == 'color_sample'
        assert data['entity_id'] == color_sample.id
        assert data['signer'] == user.username
    
    def test_export_without_signature(self, color_sample):
        """Test export fails gracefully without signature"""
        proof = export_signature_proof(color_sample)
        
        assert proof is not None
        data = json.loads(proof)
        assert 'error' in data
        assert 'no digital signature' in data['error'].lower()


@pytest.mark.django_db
class TestModelIntegration:
    """Test integration with ColorSample and ChangeOrder models"""
    
    def test_color_sample_approve_creates_signature(self, color_sample, user):
        """Test that approving color sample creates digital signature"""
        color_sample.approve(
            user=user,
            ip_address='192.168.1.1',
            signature_canvas_data='test_data',
            user_agent='Mozilla/5.0',
            geolocation={'lat': 40.7128, 'lng': -74.0060}
        )
        
        assert color_sample.status == 'approved'
        assert color_sample.approved_by == user
        assert color_sample.digital_signature is not None
        assert color_sample.digital_signature.signer == user
        assert color_sample.digital_signature.ip_address == '192.168.1.1'
    
    def test_color_sample_verify_signature_method(self, color_sample, user):
        """Test ColorSample.verify_signature() method"""
        signature = create_signature(
            entity=color_sample,
            signer=user
        )
        color_sample.digital_signature = signature
        color_sample.save()
        
        is_valid, message = color_sample.verify_signature()
        
        assert is_valid is True
        assert 'no tampering detected' in message.lower()
    
    def test_change_order_sign_document(self, change_order, user):
        """Test ChangeOrder.sign_document() method"""
        signature = change_order.sign_document(
            signer=user,
            ip_address='10.0.0.1',
            signature_canvas_data='test_data'
        )
        
        assert signature is not None
        assert change_order.digital_signature == signature
        assert signature.entity_type == 'change_order'
        assert signature.entity_id == change_order.id
    
    def test_change_order_verify_signature_method(self, change_order, user):
        """Test ChangeOrder.verify_signature() method"""
        change_order.sign_document(signer=user)
        
        is_valid, message = change_order.verify_signature()
        
        assert is_valid is True
        assert 'no tampering detected' in message.lower()


@pytest.mark.django_db
class TestSignatureSnapshot:
    """Test document snapshot generation"""
    
    def test_color_sample_snapshot_includes_key_fields(self, color_sample):
        """Test ColorSample snapshot includes all critical fields"""
        snapshot = color_sample.get_signature_snapshot()
        
        assert 'id' in snapshot
        assert 'project_id' in snapshot
        assert 'code' in snapshot
        assert 'name' in snapshot
        assert 'brand' in snapshot
        assert 'status' in snapshot
        assert 'version' in snapshot
        
        assert snapshot['id'] == color_sample.id
        assert snapshot['code'] == color_sample.code
        assert snapshot['name'] == color_sample.name
    
    def test_change_order_snapshot_includes_key_fields(self, change_order):
        """Test ChangeOrder snapshot includes all critical fields"""
        snapshot = change_order.get_signature_snapshot()
        
        assert 'id' in snapshot
        assert 'project_id' in snapshot
        assert 'description' in snapshot
        assert 'amount' in snapshot
        assert 'status' in snapshot
        
        assert snapshot['id'] == change_order.id
        assert snapshot['amount'] == str(change_order.amount)
    
    def test_snapshot_changes_invalidate_signature(self, color_sample, user):
        """Test that modifying snapshot invalidates signature"""
        # Create and verify signature
        signature = create_signature(entity=color_sample, signer=user)
        color_sample.digital_signature = signature
        color_sample.save()
        
        is_valid, _ = verify_signature(color_sample)
        assert is_valid is True
        
        # Modify the snapshot
        signature.document_snapshot['code'] = 'MODIFIED'
        signature.save()
        
        # Verification should now fail
        is_valid, message = verify_signature(color_sample)
        assert is_valid is False
        assert 'tamper detected' in message.lower()


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_signature_with_minimal_data(self, color_sample, user):
        """Test signature creation with minimal required data"""
        signature = create_signature(
            entity=color_sample,
            signer=user
        )
        
        assert signature is not None
        assert signature.signed_hash is not None
    
    def test_signature_with_none_ip_address(self, color_sample, user):
        """Test signature accepts None for optional IP address"""
        signature = create_signature(
            entity=color_sample,
            signer=user,
            ip_address=None
        )
        
        assert signature is not None
        assert signature.ip_address is None
    
    def test_hash_consistency(self, color_sample, user):
        """Test that same snapshot produces same hash"""
        signature1 = create_signature(entity=color_sample, signer=user)
        hash1 = signature1.signed_hash
        
        # Create another signature with same snapshot
        signature2 = create_signature(entity=color_sample, signer=user)
        hash2 = signature2.signed_hash
        
        # Hashes should be identical for identical snapshots
        assert hash1 == hash2
    
    def test_signature_str_representation(self, color_sample, user):
        """Test DigitalSignature __str__ method"""
        signature = create_signature(entity=color_sample, signer=user)
        
        str_repr = str(signature)
        assert 'DigitalSignature' in str_repr
        assert 'color_sample' in str_repr
        assert str(color_sample.id) in str_repr
        assert user.username in str_repr
