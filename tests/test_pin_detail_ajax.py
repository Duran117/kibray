import json
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from core.models import Project, FloorPlan, PlanPin

pytestmark = pytest.mark.django_db

@pytest.fixture
def user(client):
    U = get_user_model()
    u = U.objects.create_user(username='tester', password='pw12345')
    client.login(username='tester', password='pw12345')
    return u

@pytest.fixture
def project(user):
    return Project.objects.create(name='Demo Project', client='ClientX', start_date=date.today())

@pytest.fixture
def floor_plan(project, user, tmp_path):
    # Crear imagen mínima
    image_content = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\n\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    img = SimpleUploadedFile('plan.gif', image_content, content_type='image/gif')
    return FloorPlan.objects.create(project=project, name='Nivel 1', image=img, created_by=None)

@pytest.fixture
def pin(floor_plan, user):
    return PlanPin.objects.create(plan=floor_plan, x=0.25, y=0.75, title='Test Pin', description='Desc')

def test_pin_detail_ajax_json_structure(client, user, pin):
    url = reverse('pin_detail_ajax', args=[pin.id])
    resp = client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert resp.status_code == 200
    data = json.loads(resp.content)
    for key in ['id','title','description','type','color','task','color_sample','links']:
        assert key in data
    assert data['id'] == pin.id
    assert data['title'] == 'Test Pin'
    assert data['description'] == 'Desc'
    assert data['task'] is None
    assert isinstance(data['links'], dict)
