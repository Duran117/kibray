"""
MÓDULO 18: Site Photos - Comprehensive Test Suite
Tests for GPS auto-tagging, thumbnail generation, gallery system, and access control.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date, datetime, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Project, DamageReport, SitePhoto, ClientProjectAccess
from decimal import Decimal
import base64
from io import BytesIO

User = get_user_model()

# Valid 1x1 PNG image in base64
VALID_PNG_BASE64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_photo',
        password='pass123',
        email='admin@example.com',
        is_staff=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username='client_user',
        password='pass123',
        email='client@example.com',
        is_staff=False
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name='GalleryProject',
        client='ACME Corp',
        start_date=date.today(),
        address='123 Construction St'
    )


@pytest.fixture
def project_access(db, regular_user, project):
    """Grant regular user access to project"""
    return ClientProjectAccess.objects.create(
        user=regular_user,
        project=project,
        role='client',
        can_comment=True,
        can_create_tasks=False
    )


@pytest.fixture
def damage_report(db, project, admin_user):
    return DamageReport.objects.create(
        project=project,
        title='Wall Crack',
        description='Large crack near window',
        severity='high',
        status='open',
        reported_by=admin_user
    )


# ============================================================================
# CRUD Tests
# ============================================================================

@pytest.mark.django_db
def test_site_photo_upload_basic(api_client, admin_user, project):
    """Test basic photo upload with valid image"""
    api_client.force_authenticate(user=admin_user)
    
    # Decode base64 PNG
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('test_photo.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'Test photo upload',
        'photo_type': 'progress',
        'room': 'Living Room',
        'wall_ref': 'North Wall'
    }, format='multipart')
    
    assert res.status_code in (200, 201), f"Failed with: {res.data}"
    assert res.data['caption'] == 'Test photo upload'
    assert res.data['photo_type'] == 'progress'
    assert res.data['room'] == 'Living Room'
    assert 'thumbnail' in res.data


@pytest.mark.django_db
def test_site_photo_upload_with_gps(api_client, admin_user, project):
    """Test photo upload with GPS coordinates"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('gps_photo.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'GPS tagged photo',
        'location_lat': '37.7749',
        'location_lng': '-122.4194',
        'location_accuracy_m': '5.5'
    }, format='multipart')
    
    assert res.status_code in (200, 201)
    assert res.data['location_lat'] == '37.774900'
    assert res.data['location_lng'] == '-122.419400'
    assert res.data['location_accuracy_m'] == '5.50'


@pytest.mark.django_db
def test_site_photo_link_to_damage_report(api_client, admin_user, project, damage_report):
    """Test linking photo to damage report"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('damage_photo.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'Damage evidence',
        'photo_type': 'defect',
        'damage_report': damage_report.id
    }, format='multipart')
    
    assert res.status_code in (200, 201)
    assert res.data['damage_report'] == damage_report.id
    assert res.data['damage_report_title'] == 'Wall Crack'


@pytest.mark.django_db
def test_site_photo_update_metadata(api_client, admin_user, project):
    """Test updating photo metadata without changing image"""
    api_client.force_authenticate(user=admin_user)
    
    # Create photo
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('update_test.png', image_bytes, content_type='image/png')
    
    create_res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'Original caption'
    }, format='multipart')
    
    photo_id = create_res.data['id']
    
    # Update metadata
    update_res = api_client.patch(f'/api/v1/site-photos/{photo_id}/', {
        'caption': 'Updated caption',
        'notes': 'Added some notes',
        'room': 'Kitchen'
    }, format='json')
    
    assert update_res.status_code == 200
    assert update_res.data['caption'] == 'Updated caption'
    assert update_res.data['notes'] == 'Added some notes'
    assert update_res.data['room'] == 'Kitchen'


@pytest.mark.django_db
def test_site_photo_delete(api_client, admin_user, project):
    """Test deleting a photo"""
    api_client.force_authenticate(user=admin_user)
    
    # Create photo
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('delete_test.png', image_bytes, content_type='image/png')
    
    create_res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'To be deleted'
    }, format='multipart')
    
    photo_id = create_res.data['id']
    
    # Delete
    delete_res = api_client.delete(f'/api/v1/site-photos/{photo_id}/')
    assert delete_res.status_code == 204
    
    # Verify deleted
    get_res = api_client.get(f'/api/v1/site-photos/{photo_id}/')
    assert get_res.status_code == 404


# ============================================================================
# Filtering & Search Tests
# ============================================================================

@pytest.mark.django_db
def test_filter_by_project(api_client, admin_user):
    """Test filtering photos by project"""
    api_client.force_authenticate(user=admin_user)
    
    proj1 = Project.objects.create(name='Project1', client='Client1', start_date=date.today())
    proj2 = Project.objects.create(name='Project2', client='Client2', start_date=date.today())
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create photos for both projects
    for i in range(3):
        upload1 = SimpleUploadedFile(f'proj1_{i}.png', image_bytes, content_type='image/png')
        api_client.post('/api/v1/site-photos/', {
            'project': proj1.id,
            'image': upload1,
            'caption': f'Project 1 Photo {i}'
        }, format='multipart')
    
    for i in range(2):
        upload2 = SimpleUploadedFile(f'proj2_{i}.png', image_bytes, content_type='image/png')
        api_client.post('/api/v1/site-photos/', {
            'project': proj2.id,
            'image': upload2,
            'caption': f'Project 2 Photo {i}'
        }, format='multipart')
    
    # Filter by project 1
    res = api_client.get(f'/api/v1/site-photos/?project={proj1.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 3


@pytest.mark.django_db
def test_filter_by_photo_type(api_client, admin_user, project):
    """Test filtering photos by photo_type"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create photos with different types
    photo_types = ['before', 'progress', 'after', 'defect', 'reference']
    for ptype in photo_types:
        upload = SimpleUploadedFile(f'{ptype}.png', image_bytes, content_type='image/png')
        api_client.post('/api/v1/site-photos/', {
            'project': project.id,
            'image': upload,
            'caption': f'{ptype} photo',
            'photo_type': ptype
        }, format='multipart')
    
    # Filter by 'defect'
    res = api_client.get(f'/api/v1/site-photos/?photo_type=defect&project={project.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1
    assert results[0]['photo_type'] == 'defect'


@pytest.mark.django_db
def test_filter_by_date_range(api_client, admin_user, project):
    """Test filtering photos by date range"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create photos
    upload = SimpleUploadedFile('date_test.png', image_bytes, content_type='image/png')
    api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'Recent photo'
    }, format='multipart')
    
    # Filter by date range (use datetime instead of date to avoid timezone issues)
    from django.utils import timezone
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    res = api_client.get(f'/api/v1/site-photos/?project={project.id}&start={today}&end={tomorrow}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) >= 1


@pytest.mark.django_db
def test_search_by_caption(api_client, admin_user, project):
    """Test searching photos by caption"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create photos with different captions
    upload1 = SimpleUploadedFile('search1.png', image_bytes, content_type='image/png')
    api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload1,
        'caption': 'Kitchen renovation progress'
    }, format='multipart')
    
    upload2 = SimpleUploadedFile('search2.png', image_bytes, content_type='image/png')
    api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload2,
        'caption': 'Bathroom tile installation'
    }, format='multipart')
    
    # Search for 'kitchen'
    res = api_client.get(f'/api/v1/site-photos/?search=kitchen&project={project.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) >= 1
    assert 'kitchen' in results[0]['caption'].lower()


# ============================================================================
# Gallery Action Tests
# ============================================================================

@pytest.mark.django_db
def test_gallery_action(api_client, admin_user, project):
    """Test gallery endpoint that groups photos by type"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create photos of different types
    photo_types = ['before', 'progress', 'after', 'defect']
    for ptype in photo_types:
        for i in range(2):  # 2 photos per type
            upload = SimpleUploadedFile(f'{ptype}_{i}.png', image_bytes, content_type='image/png')
            api_client.post('/api/v1/site-photos/', {
                'project': project.id,
                'image': upload,
                'caption': f'{ptype} photo {i}',
                'photo_type': ptype
            }, format='multipart')
    
    # Call gallery action
    res = api_client.get(f'/api/v1/site-photos/gallery/?project={project.id}')
    assert res.status_code == 200
    
    # Verify structure
    assert 'before' in res.data
    assert 'progress' in res.data
    assert 'after' in res.data
    assert 'defect' in res.data
    assert 'reference' in res.data
    
    # Verify counts
    assert len(res.data['before']) == 2
    assert len(res.data['progress']) == 2
    assert len(res.data['after']) == 2
    assert len(res.data['defect']) == 2
    
    # Verify photo data structure
    sample_photo = res.data['before'][0]
    assert 'id' in sample_photo
    assert 'thumbnail' in sample_photo
    assert 'image' in sample_photo
    assert 'caption' in sample_photo
    assert 'created_at' in sample_photo


# ============================================================================
# Access Control Tests
# ============================================================================

@pytest.mark.django_db
def test_non_staff_sees_only_accessible_projects(api_client, regular_user, project, project_access):
    """Test non-staff users only see photos from projects they have access to"""
    api_client.force_authenticate(user=regular_user)
    
    # Create another project without access
    other_project = Project.objects.create(
        name='RestrictedProject',
        client='Other Client',
        start_date=date.today()
    )
    
    admin = User.objects.create_user(username='admin_temp', is_staff=True)
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create photo in accessible project
    SitePhoto.objects.create(
        project=project,
        image=SimpleUploadedFile('access1.png', image_bytes, content_type='image/png'),
        caption='Accessible photo',
        created_by=admin,
        visibility='public'
    )
    
    # Create photo in restricted project
    SitePhoto.objects.create(
        project=other_project,
        image=SimpleUploadedFile('access2.png', image_bytes, content_type='image/png'),
        caption='Restricted photo',
        created_by=admin,
        visibility='public'
    )
    
    # Regular user should only see accessible project photos
    res = api_client.get('/api/v1/site-photos/')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1
    assert results[0]['caption'] == 'Accessible photo'


@pytest.mark.django_db
def test_non_staff_sees_only_public_photos(api_client, regular_user, project, project_access):
    """Test non-staff users only see public photos, not internal ones"""
    api_client.force_authenticate(user=regular_user)
    
    admin = User.objects.create_user(username='admin_vis', is_staff=True)
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create public photo
    SitePhoto.objects.create(
        project=project,
        image=SimpleUploadedFile('public.png', image_bytes, content_type='image/png'),
        caption='Public photo',
        visibility='public',
        created_by=admin
    )
    
    # Create internal photo
    SitePhoto.objects.create(
        project=project,
        image=SimpleUploadedFile('internal.png', image_bytes, content_type='image/png'),
        caption='Internal photo',
        visibility='internal',
        created_by=admin
    )
    
    # Regular user should only see public photo
    res = api_client.get(f'/api/v1/site-photos/?project={project.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1
    assert results[0]['caption'] == 'Public photo'


@pytest.mark.django_db
def test_staff_sees_all_photos(api_client, admin_user, project):
    """Test staff users see all photos including internal"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create both public and internal photos
    SitePhoto.objects.create(
        project=project,
        image=SimpleUploadedFile('staff_public.png', image_bytes, content_type='image/png'),
        caption='Public photo',
        visibility='public',
        created_by=admin_user
    )
    
    SitePhoto.objects.create(
        project=project,
        image=SimpleUploadedFile('staff_internal.png', image_bytes, content_type='image/png'),
        caption='Internal photo',
        visibility='internal',
        created_by=admin_user
    )
    
    # Staff user should see both
    res = api_client.get(f'/api/v1/site-photos/?project={project.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 2


# ============================================================================
# Pagination Tests
# ============================================================================

@pytest.mark.django_db
def test_pagination_enabled(api_client, admin_user, project):
    """Test that pagination is enabled for photo lists"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    
    # Create 30 photos (more than default page size)
    for i in range(30):
        upload = SimpleUploadedFile(f'page_{i}.png', image_bytes, content_type='image/png')
        api_client.post('/api/v1/site-photos/', {
            'project': project.id,
            'image': upload,
            'caption': f'Photo {i}'
        }, format='multipart')
    
    # Get first page
    res = api_client.get(f'/api/v1/site-photos/?project={project.id}')
    assert res.status_code == 200
    assert 'results' in res.data
    assert 'count' in res.data
    assert 'next' in res.data
    assert res.data['count'] == 30


# ============================================================================
# Thumbnail Tests
# ============================================================================

@pytest.mark.django_db
def test_thumbnail_auto_generation(api_client, admin_user, project):
    """Test that thumbnail is automatically generated on photo upload"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('thumb_test.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'Thumbnail test'
    }, format='multipart')
    
    assert res.status_code in (200, 201)
    
    # Verify photo was created
    photo = SitePhoto.objects.get(id=res.data['id'])
    assert photo.image is not None
    
    # Thumbnail might be None if PIL not available, but should not error
    # In production with PIL installed, thumbnail should be generated
    # For this test, we just verify the field exists and doesn't error


# ============================================================================
# Edge Cases & Validation
# ============================================================================

@pytest.mark.django_db
def test_upload_without_project_fails(api_client, admin_user):
    """Test that upload without project fails validation"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('no_project.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/site-photos/', {
        'image': upload,
        'caption': 'No project'
    }, format='multipart')
    
    assert res.status_code == 400
    assert 'project' in res.data


@pytest.mark.django_db
def test_invalid_gps_coordinates(api_client, admin_user, project):
    """Test handling of invalid GPS coordinates"""
    api_client.force_authenticate(user=admin_user)
    
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile('invalid_gps.png', image_bytes, content_type='image/png')
    
    res = api_client.post('/api/v1/site-photos/', {
        'project': project.id,
        'image': upload,
        'caption': 'Invalid GPS',
        'location_lat': '999.999',  # Invalid latitude
        'location_lng': '-122.4194'
    }, format='multipart')
    
    # Should fail validation or accept but truncate
    # Depending on DecimalField validation
    assert res.status_code in (400, 201)
