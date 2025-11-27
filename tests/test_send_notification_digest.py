import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from core.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    U = get_user_model()
    return U.objects.create_user(username="client", password="pw", email="client@example.com")


def test_send_notification_digest_dry_run(user, capsys):
    # Crear notificaciones no leídas recientes
    for i in range(3):
        Notification.objects.create(
            user=user, title=f"N{i+1}", message="Hola", is_read=False, created_at=timezone.now()
        )
    out = io.StringIO()
    call_command("send_notification_digest", "--dry-run", stdout=out)
    stdout = out.getvalue()
    assert "Digest run complete" in stdout
