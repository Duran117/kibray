import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone


@pytest.mark.django_db
def test_material_request_rejects_submitted(django_user_model):
    from core.models import MaterialRequest, Project

    user = django_user_model.objects.create_user(username="mrtester", password="x")
    project = Project.objects.create(name="MatProj", client="ClientZ", start_date=timezone.now().date())

    # Intento crear con estado deprecated
    with pytest.raises(ValidationError) as exc:
        MaterialRequest.objects.create(project=project, requested_by=user, status="submitted", needed_when="now")
    assert "submitted" in str(exc.value)


@pytest.mark.django_db
def test_material_request_allows_pending(django_user_model):
    from core.models import MaterialRequest, Project

    user = django_user_model.objects.create_user(username="mrtester2", password="x")
    project = Project.objects.create(name="MatProj2", client="ClientA", start_date=timezone.now().date())

    mr = MaterialRequest.objects.create(project=project, requested_by=user, status="pending", needed_when="now")
    assert mr.status == "pending"
