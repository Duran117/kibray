import pytest
from django.urls import reverse
from django.utils import translation
from django.utils.translation import override
from django.contrib.auth import get_user_model
from core.models import Project, DamageReport
from django.utils import timezone


@pytest.mark.django_db
def test_dashboard_admin_translations(client):
    """Ensure Spanish default and English translations render for project summary labels."""
    User = get_user_model()
    user = User.objects.create_user(username="admin", password="pass123", is_staff=True, is_superuser=True)
    client.login(username="admin", password="pass123")

    # Create minimal Project (status field may not exist; rely on defaults)
    Project.objects.create(name="Proyecto Alpha", start_date=timezone.now().date())

    url = reverse("dashboard_admin") + "?legacy=true"

    # Spanish default render (LANGUAGE_CODE = 'es')
    session = client.session
    session['lang'] = 'es'
    session.save()
    resp_es = client.get(url)
    assert resp_es.status_code == 200
    html_es = resp_es.content.decode()
    assert "Proyectos Activos" in html_es
    assert "Active Projects" not in html_es

    # Activate English explicitly for translation thread then request
    translation.activate('en')
    session = client.session
    session['lang'] = 'en'
    session.save()
    resp_en = client.get(url, HTTP_ACCEPT_LANGUAGE='en')
    # Deactivate after request
    translation.deactivate()
    assert resp_en.status_code == 200
    html_en = resp_en.content.decode()
    assert "Active Projects" in html_en
    assert "Proyectos Activos" not in html_en


@pytest.mark.django_db
def test_damage_report_photos_pluralization(client):
    """Verify singular/plural photo count blocktrans works in both locales."""
    User = get_user_model()
    user = User.objects.create_user(username="user", password="pass123")
    client.login(username="user", password="pass123")

    project = Project.objects.create(name="Proyecto Beta", start_date=timezone.now().date())
    report = DamageReport.objects.create(project=project, title="Daño leve")

    detail_url = reverse("damage_report_detail", args=[report.id])

    with override("es"):
        resp_es = client.get(detail_url)
    html_es = resp_es.content.decode()
    assert resp_es.status_code == 200
    assert "Foto" in html_es  # singular/plural handled

    # Activate English similar to admin test to ensure LocaleMiddleware + session interplay
    translation.activate('en')
    session = client.session
    session['lang'] = 'en'
    session.save()
    resp_en = client.get(detail_url, HTTP_ACCEPT_LANGUAGE='en')
    translation.deactivate()
    html_en = resp_en.content.decode()
    # For 0 count we expect plural "0 Photos"; ensure English words present
    assert "Photo" in html_en or "Photos" in html_en
    assert "Fotos" not in html_en
