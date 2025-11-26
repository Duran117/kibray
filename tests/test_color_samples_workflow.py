"""
MÓDULO 19: Color Samples - Comprehensive Test Suite
Tests for KPISM numbering, approval workflow, digital signatures, and room grouping.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Project, ColorSample, ClientProjectAccess
import base64

User = get_user_model()

# Valid 1x1 PNG image
VALID_PNG_BASE64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_colors',
        password='pass123',
        email='admin@example.com',
        is_staff=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username='client_colors',
        password='pass123',
        email='client@example.com',
        is_staff=False
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name='Color Approval Project',
        client='KPIS Construction',
        start_date=date.today(),
        address='456 Design Ave'
    )


@pytest.fixture
def project_access(db, regular_user, project):
    """Grant regular user access to project"""
    return ClientProjectAccess.objects.create(
        user=regular_user,
        project=project,
        role='client',
        can_comment=True
    )


# ============================================================================
# KPISM Numbering Tests
# ============================================================================

@pytest.mark.django_db
def test_sample_number_auto_generation(api_client, admin_user, project):
    """Test automatic KPISM sample number generation"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('sample.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/color-samples/', {
        'project': project.id,
        'name': 'Warm White',
        'code': 'SW7005',
        'brand': 'Sherwin Williams',
        'sample_image': upload
    }, format='multipart')
    
    assert res.status_code in (200, 201), f"Failed: {res.data}"
    assert 'sample_number' in res.data
    assert res.data['sample_number'].startswith('KPIS')  # Client prefix
    assert res.data['sample_number'].endswith('M00001')  # First sample


@pytest.mark.django_db
def test_sample_number_sequential(api_client, admin_user, project):
    """Test sequential sample number generation"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create 3 samples
    sample_numbers = []
    for i in range(3):
        upload = SimpleUploadedFile(f'sample{i}.png', image_bytes, content_type='image/png')
        res = api_client.post('/api/v1/color-samples/', {
            'project': project.id,
            'name': f'Sample {i}',
            'code': f'CODE{i}',
            'sample_image': upload
        }, format='multipart')
        sample_numbers.append(res.data['sample_number'])
    
    # Verify sequential
    assert sample_numbers[0].endswith('M00001')
    assert sample_numbers[1].endswith('M00002')
    assert sample_numbers[2].endswith('M00003')


@pytest.mark.django_db
def test_sample_number_unique_per_project(api_client, admin_user):
    """Test sample numbers are project-scoped"""
    api_client.force_authenticate(user=admin_user)
    
    proj1 = Project.objects.create(name='Proj1', client='ACME', start_date=date.today())
    proj2 = Project.objects.create(name='Proj2', client='BETA', start_date=date.today())
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create sample in proj1
    upload1 = SimpleUploadedFile('p1.png', image_bytes, content_type='image/png')
    res1 = api_client.post('/api/v1/color-samples/', {
        'project': proj1.id,
        'name': 'P1 Sample',
        'sample_image': upload1
    }, format='multipart')
    
    # Create sample in proj2
    upload2 = SimpleUploadedFile('p2.png', image_bytes, content_type='image/png')
    res2 = api_client.post('/api/v1/color-samples/', {
        'project': proj2.id,
        'name': 'P2 Sample',
        'sample_image': upload2
    }, format='multipart')
    
    # Both should be M00001 (separate counters per project)
    assert res1.data['sample_number'].endswith('M00001')
    assert res2.data['sample_number'].endswith('M00001')
    
    # Different client prefixes
    assert res1.data['sample_number'].startswith('ACME')
    assert res2.data['sample_number'].startswith('BETA')


# ============================================================================
# Approval Workflow Tests
# ============================================================================

@pytest.mark.django_db
def test_approve_color_sample(api_client, admin_user, project):
    """Test approving a color sample with digital signature"""
    api_client.force_authenticate(user=admin_user)
    
    # Create sample
    sample = ColorSample.objects.create(
        project=project,
        name='Approved Color',
        code='SW1234',
        status='proposed',
        created_by=admin_user
    )
    
    # Approve
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/approve/', {
        'signature_ip': '192.168.1.100'
    })
    
    assert res.status_code == 200
    assert res.data['status'] == 'approved'
    assert res.data['approved_by'] == admin_user.id
    assert res.data['approved_at'] is not None
    assert res.data['approval_signature'] is not None  # SHA256 hash
    assert res.data['approval_ip'] == '192.168.1.100'


@pytest.mark.django_db
def test_reject_color_sample_with_reason(api_client, admin_user, project):
    """Test rejecting a color sample with required reason"""
    api_client.force_authenticate(user=admin_user)
    
    # Create sample
    sample = ColorSample.objects.create(
        project=project,
        name='Rejected Color',
        code='SW5678',
        status='review',
        created_by=admin_user
    )
    
    # Reject with reason
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/reject/', {
        'reason': 'Color does not match design requirements'
    })
    
    assert res.status_code == 200
    assert res.data['status'] == 'rejected'
    assert res.data['rejected_by'] == admin_user.id
    assert res.data['rejected_at'] is not None
    assert res.data['rejection_reason'] == 'Color does not match design requirements'


@pytest.mark.django_db
def test_reject_without_reason_fails(api_client, admin_user, project):
    """Test rejecting without reason fails validation"""
    api_client.force_authenticate(user=admin_user)
    
    sample = ColorSample.objects.create(
        project=project,
        name='Test Sample',
        status='proposed',
        created_by=admin_user
    )
    
    # Reject without reason
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/reject/', {})
    
    assert res.status_code == 400
    assert 'reason' in res.data


@pytest.mark.django_db
def test_request_changes(api_client, admin_user, project):
    """Test requesting changes moves sample to review status"""
    api_client.force_authenticate(user=admin_user)
    
    sample = ColorSample.objects.create(
        project=project,
        name='Under Review',
        status='proposed',
        created_by=admin_user
    )
    
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/request-changes/', {
        'notes': 'Please make it slightly darker'
    })
    
    assert res.status_code == 200
    assert res.data['status'] == 'review'
    assert 'Please make it slightly darker' in res.data['client_notes']


@pytest.mark.django_db
def test_cannot_approve_already_approved(api_client, admin_user, project):
    """Test cannot approve an already approved sample"""
    api_client.force_authenticate(user=admin_user)
    
    sample = ColorSample.objects.create(
        project=project,
        name='Already Approved',
        status='approved',
        approved_by=admin_user,
        created_by=admin_user
    )
    
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/approve/', {})
    
    assert res.status_code == 400
    assert 'already approved' in res.data['error'].lower()


@pytest.mark.django_db
def test_cannot_reject_already_rejected(api_client, admin_user, project):
    """Test cannot reject an already rejected sample"""
    api_client.force_authenticate(user=admin_user)
    
    sample = ColorSample.objects.create(
        project=project,
        name='Already Rejected',
        status='rejected',
        rejected_by=admin_user,
        rejection_reason='Original reason',
        created_by=admin_user
    )
    
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/reject/', {
        'reason': 'New reason'
    })
    
    assert res.status_code == 400
    assert 'already rejected' in res.data['error'].lower()


# ============================================================================
# Room Grouping Tests
# ============================================================================

@pytest.mark.django_db
def test_room_grouping(api_client, admin_user, project):
    """Test grouping samples by room"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create samples for kitchen
    for i in range(3):
        upload = SimpleUploadedFile(f'kitchen{i}.png', image_bytes, content_type='image/png')
        api_client.post('/api/v1/color-samples/', {
            'project': project.id,
            'name': f'Kitchen Color {i}',
            'room_location': 'Kitchen',
            'room_group': 'Kitchen',
            'sample_image': upload
        }, format='multipart')
    
    # Filter by room_group
    res = api_client.get(f'/api/v1/color-samples/?project={project.id}&room_group=Kitchen')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 3


# ============================================================================
# Filtering & Search Tests
# ============================================================================

@pytest.mark.django_db
def test_filter_by_status(api_client, admin_user, project):
    """Test filtering samples by status"""
    api_client.force_authenticate(user=admin_user)
    
    # Create samples with different statuses
    ColorSample.objects.create(project=project, name='Proposed', status='proposed', created_by=admin_user)
    ColorSample.objects.create(project=project, name='Approved', status='approved', created_by=admin_user)
    ColorSample.objects.create(project=project, name='Rejected', status='rejected', created_by=admin_user)
    
    # Filter by approved
    res = api_client.get(f'/api/v1/color-samples/?project={project.id}&status=approved')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1
    assert results[0]['status'] == 'approved'


@pytest.mark.django_db
def test_search_by_name_or_code(api_client, admin_user, project):
    """Test searching samples by name or code"""
    api_client.force_authenticate(user=admin_user)
    
    ColorSample.objects.create(project=project, name='Navajo White', code='SW6126', created_by=admin_user)
    ColorSample.objects.create(project=project, name='Alabaster', code='SW7008', created_by=admin_user)
    
    # Search for 'navajo'
    res = api_client.get(f'/api/v1/color-samples/?search=navajo&project={project.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) >= 1
    assert 'navajo' in results[0]['name'].lower()


# ============================================================================
# Access Control Tests
# ============================================================================

@pytest.mark.django_db
def test_non_staff_sees_only_accessible_projects(api_client, regular_user, project, project_access):
    """Test non-staff users only see samples from accessible projects"""
    api_client.force_authenticate(user=regular_user)
    
    # Create another project without access
    other_project = Project.objects.create(name='Restricted', client='Other', start_date=date.today())
    
    admin = User.objects.create_user(username='admin_temp', is_staff=True)
    
    # Create samples in both projects
    ColorSample.objects.create(project=project, name='Accessible', created_by=admin)
    ColorSample.objects.create(project=other_project, name='Restricted', created_by=admin)
    
    # Regular user should only see accessible project sample
    res = api_client.get('/api/v1/color-samples/')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1
    assert results[0]['name'] == 'Accessible'


# ============================================================================
# CRUD Tests
# ============================================================================

@pytest.mark.django_db
def test_create_sample_with_metadata(api_client, admin_user, project):
    """Test creating sample with all metadata"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    sample_image = SimpleUploadedFile('sample.png', image_bytes, content_type='image/png')
    ref_image = SimpleUploadedFile('ref.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/color-samples/', {
        'project': project.id,
        'name': 'Perfect White',
        'code': 'SW7010',
        'brand': 'Sherwin Williams',
        'finish': 'Matte',
        'gloss': 'Flat',
        'room_location': 'Living Room',
        'room_group': 'Living Area',
        'notes': 'Primary color for walls',
        'sample_image': sample_image,
        'reference_photo': ref_image
    }, format='multipart')
    
    assert res.status_code in (200, 201)
    assert res.data['name'] == 'Perfect White'
    assert res.data['sample_number'] is not None
    assert res.data['status'] == 'proposed'  # Default status


@pytest.mark.django_db
def test_update_sample_metadata(api_client, admin_user, project):
    """Test updating sample metadata"""
    api_client.force_authenticate(user=admin_user)
    
    sample = ColorSample.objects.create(
        project=project,
        name='Original Name',
        created_by=admin_user
    )
    
    res = api_client.patch(f'/api/v1/color-samples/{sample.id}/', {
        'name': 'Updated Name',
        'notes': 'Added notes'
    }, format='json')
    
    assert res.status_code == 200
    assert res.data['name'] == 'Updated Name'
    assert res.data['notes'] == 'Added notes'


@pytest.mark.django_db
def test_delete_sample(api_client, admin_user, project):
    """Test deleting a color sample"""
    api_client.force_authenticate(user=admin_user)
    
    sample = ColorSample.objects.create(
        project=project,
        name='To Delete',
        created_by=admin_user
    )
    
    res = api_client.delete(f'/api/v1/color-samples/{sample.id}/')
    assert res.status_code == 204
    
    # Verify deleted
    assert not ColorSample.objects.filter(id=sample.id).exists()


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.django_db
def test_create_without_project_fails(api_client, admin_user):
    """Test creating sample without project fails"""
    api_client.force_authenticate(user=admin_user)
    
    res = api_client.post('/api/v1/color-samples/', {
        'name': 'No Project Sample'
    }, format='json')
    
    assert res.status_code == 400
    assert 'project' in res.data


@pytest.mark.django_db
def test_pagination_enabled(api_client, admin_user, project):
    """Test that pagination is enabled"""
    api_client.force_authenticate(user=admin_user)
    
    # Create 30 samples
    for i in range(30):
        ColorSample.objects.create(
            project=project,
            name=f'Sample {i}',
            created_by=admin_user
        )
    
    res = api_client.get(f'/api/v1/color-samples/?project={project.id}')
    assert res.status_code == 200
    assert 'results' in res.data
    assert 'count' in res.data
    assert res.data['count'] == 30
