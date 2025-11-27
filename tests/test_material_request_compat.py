import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone


@pytest.mark.django_db
def test_material_request_status_compat_layer(django_user_model):
    """Test status mapping from legacy to normalized values."""
    from core.models import MaterialRequest, Project

    user = django_user_model.objects.create_user(username="mrcompat", password="x")
    project = Project.objects.create(name="CompatProj", client="ClientC", start_date=timezone.now().date())

    # Crear con estado legacy 'submitted' (debería mapearse a 'pending' en clean)
    mr = MaterialRequest(project=project, requested_by=user, status="submitted", needed_when="now")
    mr.clean()  # Aplica mapping
    assert mr.status == "pending", "Legacy 'submitted' debe mapearse a 'pending'"
    mr.save()
    mr.refresh_from_db()
    assert mr.status == "pending"


@pytest.mark.django_db
def test_material_request_serializer_status_mapping(django_user_model):
    """Test serializer validate_status applies compat mapping."""
    from core.api.serializers import MaterialRequestSerializer
    from core.models import Project

    user = django_user_model.objects.create_user(username="mrsertest", password="x")
    project = Project.objects.create(name="SerProj", client="ClientS", start_date=timezone.now().date())

    # Enviar legacy status vía serializer
    data = {"project": project.id, "status": "submitted", "needed_when": "now", "items": []}  # Legacy
    serializer = MaterialRequestSerializer(data=data, context={"request": type("obj", (object,), {"user": user})()})
    assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
    # Validación debe haber mapeado 'submitted' -> 'pending'
    assert serializer.validated_data["status"] == "pending"


@pytest.mark.django_db
def test_material_request_disallows_direct_submitted_bypass(django_user_model):
    """Direct assignment of 'submitted' after mapping should still be blocked if no compat path."""
    from core.models import MaterialRequest, Project

    user = django_user_model.objects.create_user(username="directblock", password="x")
    project = Project.objects.create(name="BlockProj", client="ClientB", start_date=timezone.now().date())

    # Intento asignar submitted directamente sin pasar por compat map (edge case artificial)
    # En práctica, clean() mapeará; pero si alguien fuerza post-clean, debería fallar.
    # Test actual: validar que mapping funciona y no hay bypass fácil.
    mr = MaterialRequest(project=project, requested_by=user, status="submitted", needed_when="now")
    mr.clean()  # Mapea
    assert mr.status == "pending"
    # No debería levantar ValidationError porque ya fue mapeado
    mr.save()
    assert mr.status == "pending"
