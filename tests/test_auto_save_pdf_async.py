"""
Async ``auto_save_pdf_async`` migration — tests
================================================

Covers the move of the heavy ``auto_save_*_pdf`` helpers (Invoice / Estimate
/ ChangeOrder / ColorSample) out of the request thread.

* The generic Celery task ``core.tasks.auto_save_pdf_async`` dispatches to
  the right ``document_storage_service`` helper by ``doc_kind``, filters
  unsafe kwargs, handles missing instances, and retries transient failures.
* The status-flip view ``invoice_mark_sent`` now enqueues the helper via
  ``transaction.on_commit`` instead of running it inline.
"""

import uuid
from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import Client as TestClient
from django.urls import reverse

from core.models import Invoice, Project
from core.tasks import auto_save_pdf_async, _AUTO_SAVE_PDF_DISPATCH

pytestmark = pytest.mark.django_db


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="autoadmin", password="pw", is_staff=True
    )


@pytest.fixture
def project(db):
    return Project.objects.create(name="Async AutoSave Project")


@pytest.fixture
def invoice(project):
    return Invoice.objects.create(
        project=project,
        invoice_number=f"INV-{uuid.uuid4().hex[:6]}",
        total_amount=Decimal("1000.00"),
        status="DRAFT",
    )


# ─── Generic Celery task ─────────────────────────────────────────────


class TestAutoSavePdfAsyncTask:
    def test_dispatch_table_covers_all_kinds(self):
        assert set(_AUTO_SAVE_PDF_DISPATCH) == {
            "invoice",
            "estimate",
            "changeorder",
            "colorsample",
        }

    def test_unknown_doc_kind_returns_error(self):
        result = auto_save_pdf_async.run(
            doc_kind="potato", doc_id=1, user_id=None
        )
        assert result == {"error": "unknown_doc_kind", "doc_kind": "potato"}

    def test_missing_instance_returns_error(self):
        result = auto_save_pdf_async.run(
            doc_kind="invoice", doc_id=999_999, user_id=None
        )
        assert result == {
            "error": "doc_not_found",
            "doc_kind": "invoice",
            "doc_id": 999_999,
        }

    def test_invoice_dispatch_calls_helper_with_user_and_overwrite(
        self, invoice, admin_user
    ):
        sentinel = mock.Mock(id=42)
        with mock.patch(
            "core.services.document_storage_service.auto_save_invoice_pdf",
            return_value=sentinel,
        ) as m_helper:
            result = auto_save_pdf_async.run(
                doc_kind="invoice",
                doc_id=invoice.id,
                user_id=admin_user.id,
                overwrite=True,
            )

        m_helper.assert_called_once()
        args, kwargs = m_helper.call_args
        assert args[0].pk == invoice.id
        assert kwargs["user"].pk == admin_user.id
        assert kwargs["overwrite"] is True
        assert result == {
            "doc_kind": "invoice",
            "doc_id": invoice.id,
            "project_file_id": 42,
        }

    def test_estimate_dispatch_forwards_as_contract_opt(
        self, project, admin_user
    ):
        from core.models import Estimate

        est = Estimate.objects.create(
            project=project,
            version=1,
            approved=True,
            code=f"KPTT{uuid.uuid4().hex[:4].upper()}",
        )
        sentinel = mock.Mock(id=7)
        with mock.patch(
            "core.services.document_storage_service.auto_save_estimate_pdf",
            return_value=sentinel,
        ) as m_helper:
            auto_save_pdf_async.run(
                doc_kind="estimate",
                doc_id=est.id,
                user_id=admin_user.id,
                as_contract=True,
                overwrite=True,
            )

        _, kwargs = m_helper.call_args
        assert kwargs["as_contract"] is True
        assert kwargs["overwrite"] is True

    def test_unsafe_opts_are_filtered_out(self, invoice, admin_user):
        """Helper only accepts ``overwrite`` — extra keys must NOT bubble."""
        with mock.patch(
            "core.services.document_storage_service.auto_save_invoice_pdf",
            return_value=None,
        ) as m_helper:
            auto_save_pdf_async.run(
                doc_kind="invoice",
                doc_id=invoice.id,
                user_id=admin_user.id,
                overwrite=True,
                as_contract=True,  # not allowed for invoice helper
                evil="yes",
            )

        _, kwargs = m_helper.call_args
        assert "as_contract" not in kwargs
        assert "evil" not in kwargs
        assert kwargs["overwrite"] is True

    def test_helper_returning_none_is_ok(self, invoice):
        with mock.patch(
            "core.services.document_storage_service.auto_save_invoice_pdf",
            return_value=None,
        ):
            result = auto_save_pdf_async.run(
                doc_kind="invoice", doc_id=invoice.id, user_id=None
            )
        assert result == {
            "doc_kind": "invoice",
            "doc_id": invoice.id,
            "project_file_id": None,
        }

    def test_helper_exception_retries_then_returns_error(self, invoice):
        with mock.patch(
            "core.services.document_storage_service.auto_save_invoice_pdf",
            side_effect=RuntimeError("kaboom"),
        ), mock.patch(
            "celery.app.task.Task.retry",
            side_effect=auto_save_pdf_async.MaxRetriesExceededError(),
        ):
            result = auto_save_pdf_async.run(
                doc_kind="invoice", doc_id=invoice.id, user_id=None
            )
        assert result["error"] == "generation_failed"
        assert result["doc_kind"] == "invoice"
        assert result["doc_id"] == invoice.id
        assert "kaboom" in result["exception"]

    def test_user_id_none_passes_user_none(self, invoice):
        with mock.patch(
            "core.services.document_storage_service.auto_save_invoice_pdf",
            return_value=None,
        ) as m_helper:
            auto_save_pdf_async.run(
                doc_kind="invoice", doc_id=invoice.id, user_id=None
            )
        _, kwargs = m_helper.call_args
        assert kwargs["user"] is None


# ─── invoice_mark_sent dispatch via on_commit ───────────────────────


class TestInvoiceMarkSentAsync:
    def test_mark_sent_enqueues_celery_task(self, invoice, admin_user):
        c = TestClient()
        c.login(username="autoadmin", password="pw")

        with mock.patch(
            "core.tasks.auto_save_pdf_async.delay"
        ) as m_delay, TestCase.captureOnCommitCallbacks(execute=True):
            resp = c.post(
                reverse("invoice_mark_sent", kwargs={"invoice_id": invoice.id})
            )

        assert resp.status_code in (302, 303)
        # Inline render must not be reachable here — it's gone — but the
        # Celery worker MUST have been enqueued exactly once.
        m_delay.assert_called_once()
        kwargs = m_delay.call_args.kwargs
        assert kwargs["doc_kind"] == "invoice"
        assert kwargs["doc_id"] == invoice.id
        assert kwargs["user_id"] == admin_user.id
        assert kwargs["overwrite"] is True

        # And the status flip itself committed.
        invoice.refresh_from_db()
        assert invoice.status == "SENT"
        assert invoice.sent_by_id == admin_user.id

    def test_mark_sent_noop_does_not_enqueue(self, invoice, admin_user):
        invoice.status = "SENT"
        invoice.save(update_fields=["status"])

        c = TestClient()
        c.login(username="autoadmin", password="pw")

        with mock.patch(
            "core.tasks.auto_save_pdf_async.delay"
        ) as m_delay, TestCase.captureOnCommitCallbacks(execute=True):
            c.post(
                reverse("invoice_mark_sent", kwargs={"invoice_id": invoice.id})
            )

        m_delay.assert_not_called()
