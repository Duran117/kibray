"""
Async signed-contract PDF migration — tests
============================================

Covers the move of the heavy ReportLab render out of the request thread:

* ``ContractService.sign_contract(..., async_pdf=True)`` (new default) must
  defer the render to ``core.tasks.generate_signed_contract_pdf_async`` via
  ``transaction.on_commit`` — i.e. the request thread must NOT call the
  inline ``generate_signed_contract_pdf`` helper.
* ``async_pdf=False`` keeps the legacy inline behaviour (so management
  commands / tests that need the PDF immediately still work).
* The Celery task itself loads the contract, calls the inline generator,
  attaches the resulting ``ProjectFile`` to ``contract.signed_pdf_file`` and
  notifies the user; gracefully handles missing contracts and render
  failures.
* The module-level ``sign_contract`` convenience wrapper forwards the new
  ``async_pdf`` argument.
"""

import uuid
from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Contract, Estimate, Notification, Project, ProjectFile, FileCategory
from core.services.contract_service import ContractService
from core.services import contract_service as contract_service_module

pytestmark = pytest.mark.django_db


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="signer", password="pw", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="Async Signed Contract Project")


@pytest.fixture
def estimate(project):
    return Estimate.objects.create(
        project=project,
        version=1,
        approved=True,
        code=f"KPTT{uuid.uuid4().hex[:4].upper()}",
    )


@pytest.fixture
def contract(project, estimate):
    return Contract.objects.create(
        estimate=estimate,
        project=project,
        contract_number=f"C-{uuid.uuid4().hex[:6]}",
        status="pending_signature",
        total_amount=Decimal("5000.00"),
        client_view_token=uuid.uuid4().hex,
    )


@pytest.fixture
def fake_project_file(project):
    """A real ProjectFile row we can hand back from a mocked generator."""
    from django.core.files.base import ContentFile

    cat, _ = FileCategory.objects.get_or_create(
        project=project, name="Contracts"
    )
    pf = ProjectFile(
        project=project,
        category=cat,
        name="signed.pdf",
        file_type="pdf",
    )
    pf.file.save("signed.pdf", ContentFile(b"%PDF-1.4 stub"), save=False)
    pf.save()
    return pf


# ─── ContractService.sign_contract dispatch behaviour ───────────────


class TestSignContractAsyncDispatch:
    def test_default_async_pdf_is_true(self):
        """Regression guard — async should be the new default."""
        import inspect

        sig = inspect.signature(ContractService.sign_contract)
        assert sig.parameters["async_pdf"].default is True

    def test_async_dispatch_uses_celery_delay(self, contract, user):
        """When async_pdf=True the heavy renderer must NOT run inline; the
        Celery task must be enqueued instead (via on_commit, which fires at
        the end of TestCase atomic block)."""
        with mock.patch(
            "core.tasks.generate_signed_contract_pdf_async.delay"
        ) as m_delay, mock.patch.object(
            ContractService, "generate_signed_contract_pdf"
        ) as m_inline, TestCase.captureOnCommitCallbacks(execute=True):
            ContractService.sign_contract(
                contract,
                client_name="Jane Client",
                ip_address="1.2.3.4",
                user=user,
            )

        # Inline generator must not run on the request thread.
        m_inline.assert_not_called()
        # Celery task must be enqueued exactly once with the right kwargs.
        m_delay.assert_called_once_with(contract_id=contract.id, user_id=user.id)

    def test_async_dispatch_user_id_none_when_no_user(self, contract):
        with mock.patch(
            "core.tasks.generate_signed_contract_pdf_async.delay"
        ) as m_delay, TestCase.captureOnCommitCallbacks(execute=True):
            ContractService.sign_contract(
                contract,
                client_name="Anonymous",
                user=None,
            )
        m_delay.assert_called_once_with(contract_id=contract.id, user_id=None)

    def test_inline_path_when_async_false(self, contract, user, fake_project_file):
        """async_pdf=False should keep the legacy synchronous behaviour."""
        with mock.patch(
            "core.tasks.generate_signed_contract_pdf_async.delay"
        ) as m_delay, mock.patch.object(
            ContractService,
            "generate_signed_contract_pdf",
            return_value=fake_project_file,
        ) as m_inline:
            ContractService.sign_contract(
                contract,
                client_name="Jane Client",
                user=user,
                async_pdf=False,
            )

        m_delay.assert_not_called()
        m_inline.assert_called_once()
        contract.refresh_from_db()
        assert contract.signed_pdf_file_id == fake_project_file.id

    def test_no_dispatch_when_generate_signed_pdf_false(self, contract, user):
        """If the caller explicitly disables PDF generation, neither path
        should fire."""
        with mock.patch(
            "core.tasks.generate_signed_contract_pdf_async.delay"
        ) as m_delay, mock.patch.object(
            ContractService, "generate_signed_contract_pdf"
        ) as m_inline:
            ContractService.sign_contract(
                contract,
                client_name="Jane Client",
                user=user,
                generate_signed_pdf=False,
            )

        m_delay.assert_not_called()
        m_inline.assert_not_called()

    def test_unsignable_contract_raises_before_dispatch(self, contract, user):
        contract.status = "active"  # already signed/countersigned
        contract.save(update_fields=["status"])

        with mock.patch(
            "core.tasks.generate_signed_contract_pdf_async.delay"
        ) as m_delay:
            with pytest.raises(ValueError):
                ContractService.sign_contract(
                    contract,
                    client_name="Jane",
                    user=user,
                )
        m_delay.assert_not_called()


# ─── Module-level convenience wrapper ───────────────────────────────


class TestModuleLevelWrapper:
    def test_wrapper_forwards_async_pdf(self, contract, user):
        with mock.patch.object(
            ContractService, "sign_contract", return_value=contract
        ) as m_svc:
            contract_service_module.sign_contract(
                contract,
                "Jane",
                None,
                "1.1.1.1",
                True,
                user,
                False,  # async_pdf
            )

        m_svc.assert_called_once_with(
            contract, "Jane", None, "1.1.1.1", True, user, False
        )

    def test_wrapper_default_async_pdf_true(self, contract, user):
        with mock.patch.object(
            ContractService, "sign_contract", return_value=contract
        ) as m_svc:
            contract_service_module.sign_contract(contract, "Jane", user=user)

        # Last positional argument forwarded should be async_pdf=True
        args, _ = m_svc.call_args
        assert args[-1] is True


# ─── Celery task end-to-end (with ReportLab mocked) ─────────────────


class TestGenerateSignedContractPdfAsyncTask:
    def test_unknown_contract_returns_error(self):
        from core.tasks import generate_signed_contract_pdf_async

        result = generate_signed_contract_pdf_async.run(
            contract_id=999_999, user_id=None
        )
        assert result == {"error": "contract_not_found", "contract_id": 999_999}

    def test_success_attaches_project_file_and_notifies(
        self, contract, user, fake_project_file
    ):
        from core.tasks import generate_signed_contract_pdf_async

        with mock.patch.object(
            ContractService,
            "generate_signed_contract_pdf",
            return_value=fake_project_file,
        ) as m_gen:
            result = generate_signed_contract_pdf_async.run(
                contract_id=contract.id, user_id=user.id
            )

        m_gen.assert_called_once()
        # ProjectFile attached
        contract.refresh_from_db()
        assert contract.signed_pdf_file_id == fake_project_file.id
        # Result payload
        assert result == {
            "contract_id": contract.id,
            "project_file_id": fake_project_file.id,
        }
        # Notification created for the user
        assert Notification.objects.filter(
            user=user,
            related_object_type="contract",
            related_object_id=contract.id,
        ).exists()

    def test_generator_returns_none_does_not_overwrite(self, contract, user):
        from core.tasks import generate_signed_contract_pdf_async

        with mock.patch.object(
            ContractService, "generate_signed_contract_pdf", return_value=None
        ):
            result = generate_signed_contract_pdf_async.run(
                contract_id=contract.id, user_id=user.id
            )

        contract.refresh_from_db()
        assert contract.signed_pdf_file_id is None
        assert result == {"contract_id": contract.id, "project_file_id": None}
        # No success notification when nothing was produced
        assert not Notification.objects.filter(
            user=user, related_object_id=contract.id
        ).exists()

    def test_render_exception_retries_then_notifies(self, contract, user):
        """When ReportLab keeps blowing up, after MaxRetries we must surface
        a Notification rather than raising into the worker."""
        from core.tasks import generate_signed_contract_pdf_async

        with mock.patch.object(
            ContractService,
            "generate_signed_contract_pdf",
            side_effect=RuntimeError("boom"),
        ), mock.patch(
            "celery.app.task.Task.retry",
            side_effect=generate_signed_contract_pdf_async.MaxRetriesExceededError(),
        ):
            result = generate_signed_contract_pdf_async.run(
                contract_id=contract.id, user_id=user.id
            )

        assert result["error"] == "generation_failed"
        assert result["contract_id"] == contract.id
        assert "boom" in result["exception"]
        # User notified about failure
        assert Notification.objects.filter(
            user=user, title__icontains="failed"
        ).exists()

    def test_user_id_none_skips_notification(self, contract, fake_project_file):
        from core.tasks import generate_signed_contract_pdf_async

        with mock.patch.object(
            ContractService,
            "generate_signed_contract_pdf",
            return_value=fake_project_file,
        ):
            result = generate_signed_contract_pdf_async.run(
                contract_id=contract.id, user_id=None
            )

        assert result["project_file_id"] == fake_project_file.id
        assert Notification.objects.count() == 0
