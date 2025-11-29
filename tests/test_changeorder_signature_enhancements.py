import base64
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Project, ChangeOrder

PNG_1x1_BASE64 = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def create_project():
    return Project.objects.create(
        name="Test Project", start_date=timezone.now().date(), client="Cliente Demo"
    )


def test_signature_token_valid_access(client):
    project = create_project()
    co = ChangeOrder.objects.create(project=project, description="Desc", pricing_type="FIXED", amount=50)
    token = signing.dumps({"co": co.id})
    url = reverse("changeorder_customer_signature_token", args=[co.id, token])
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"Firma Digital" in resp.content


def test_signature_token_invalid(client):
    project = create_project()
    co = ChangeOrder.objects.create(project=project, description="X", pricing_type="FIXED", amount=10)
    bad_token = signing.dumps({"co": co.id}) + "tamper"
    url = reverse("changeorder_customer_signature_token", args=[co.id, bad_token])
    resp = client.get(url)
    assert resp.status_code == 403


def test_signature_post_creates_artifacts(client):
    project = create_project()
    co = ChangeOrder.objects.create(project=project, description="Trabajo", pricing_type="FIXED", amount=75)
    url = reverse("changeorder_customer_signature", args=[co.id])
    resp = client.post(
        url,
        {
            "signer_name": "Juan Pérez",
            "signature_data": PNG_1x1_BASE64,
            "customer_email": "cliente@example.com",
        },
    )
    assert resp.status_code == 200
    co.refresh_from_db()
    assert co.signature_image, "Debe guardar imagen de firma"
    assert co.signed_pdf, "Debe generar PDF firmado"
    assert co.status == "approved"
    assert co.signed_by == "Juan Pérez"
    # IP puede ser None en test environment; user-agent se captura si presente
    assert co.signed_user_agent is not None


def test_currency_filter():
    from core.templatetags.currency_extras import currency_es

    formatted = currency_es(1234.5)
    assert formatted.startswith("$"), "Debe anteponer símbolo $"
    assert any(sep in formatted for sep in [",", "."]), "Debe contener separador de miles o decimales"
