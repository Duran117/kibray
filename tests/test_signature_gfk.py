"""Tests for Phase D4 — Signature GenericForeignKey support.

Covers:
* Model: ``content_type``/``object_id``/``content_object`` round-trip on a
  real Project instance.
* Serializer: exposes ``content_type_label`` derived field.
* List endpoint filters: ``?content_type=...``, ``?content_type_label=...``,
  ``?object_id=...`` (alone and combined; bad values short-circuit to empty).
* ``GET /api/v1/signatures/for-object/`` action — payload shape, validation
  errors (missing params, malformed label, unknown CT, non-int object_id),
  and proper isolation between objects.
* Backwards compatibility: existing signatures without GFK fields still
  work (null content_type / null object_id).
* Auth requirements preserved.
"""

from __future__ import annotations

import hashlib
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from core.models import Project
from signatures.models import Signature

pytestmark = pytest.mark.django_db


User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def signer_user():
    return User.objects.create_user(username="d4_signer", password="pw", email="d4@example.com")


@pytest.fixture
def project_a():
    return Project.objects.create(
        name="GFK Project A", client="C", start_date=date(2026, 1, 1), address="x"
    )


@pytest.fixture
def project_b():
    return Project.objects.create(
        name="GFK Project B", client="C", start_date=date(2026, 1, 1), address="y"
    )


@pytest.fixture
def api_client():
    return APIClient()


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class TestSignatureGFKModel:
    def test_attach_via_content_object(self, signer_user, project_a):
        sig = Signature.objects.create(
            signer=signer_user,
            title="Project sign-off",
            content_hash=_hash("payload"),
            content_object=project_a,
        )
        sig.refresh_from_db()
        assert sig.content_object == project_a
        assert sig.object_id == project_a.id
        assert sig.content_type == ContentType.objects.get_for_model(Project)

    def test_null_gfk_still_valid_backwards_compat(self, signer_user):
        sig = Signature.objects.create(
            signer=signer_user, title="Standalone", content_hash=_hash("x")
        )
        assert sig.content_type is None
        assert sig.object_id is None
        assert sig.content_object is None


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------


class TestSignatureSerializerExposesGFK:
    def test_content_type_label_derived(self, api_client, signer_user, project_a):
        sig = Signature.objects.create(
            signer=signer_user,
            title="t",
            content_hash=_hash("x"),
            content_object=project_a,
        )
        api_client.force_authenticate(user=signer_user)
        res = api_client.get(f"/api/v1/signatures/{sig.id}/")
        assert res.status_code == 200
        assert res.data["content_type_label"] == "core.project"
        assert res.data["object_id"] == project_a.id

    def test_content_type_label_null_when_no_gfk(self, api_client, signer_user):
        sig = Signature.objects.create(signer=signer_user, title="t", content_hash=_hash("x"))
        api_client.force_authenticate(user=signer_user)
        res = api_client.get(f"/api/v1/signatures/{sig.id}/")
        assert res.status_code == 200
        assert res.data["content_type_label"] is None


# ---------------------------------------------------------------------------
# List filters
# ---------------------------------------------------------------------------


class TestListFilters:
    def _make(self, signer, project=None, title="t"):
        return Signature.objects.create(
            signer=signer,
            title=title,
            content_hash=_hash(title),
            content_object=project,
        )

    def test_filter_by_content_type_id(self, api_client, signer_user, project_a):
        self._make(signer_user, project_a, title="one")
        self._make(signer_user, title="orphan")  # no GFK
        ct = ContentType.objects.get_for_model(Project)
        api_client.force_authenticate(user=signer_user)
        res = api_client.get(f"/api/v1/signatures/?content_type={ct.id}")
        assert res.status_code == 200
        ids = [r["id"] for r in (res.data["results"] if "results" in res.data else res.data)]
        assert len(ids) == 1

    def test_filter_by_content_type_label(self, api_client, signer_user, project_a):
        self._make(signer_user, project_a, title="lbl")
        self._make(signer_user, title="orphan")
        api_client.force_authenticate(user=signer_user)
        res = api_client.get("/api/v1/signatures/?content_type_label=core.project")
        items = res.data["results"] if "results" in res.data else res.data
        assert len(items) == 1

    def test_filter_by_object_id_isolates_targets(
        self, api_client, signer_user, project_a, project_b
    ):
        self._make(signer_user, project_a, title="a1")
        self._make(signer_user, project_a, title="a2")
        self._make(signer_user, project_b, title="b1")
        api_client.force_authenticate(user=signer_user)
        res = api_client.get(
            f"/api/v1/signatures/?content_type_label=core.project&object_id={project_a.id}"
        )
        items = res.data["results"] if "results" in res.data else res.data
        assert len(items) == 2

    def test_unknown_content_type_label_returns_empty(self, api_client, signer_user, project_a):
        self._make(signer_user, project_a)
        api_client.force_authenticate(user=signer_user)
        res = api_client.get("/api/v1/signatures/?content_type_label=core.doesnotexist")
        items = res.data["results"] if "results" in res.data else res.data
        assert items == []

    def test_invalid_object_id_returns_empty(self, api_client, signer_user, project_a):
        self._make(signer_user, project_a)
        api_client.force_authenticate(user=signer_user)
        res = api_client.get("/api/v1/signatures/?object_id=not-an-int")
        items = res.data["results"] if "results" in res.data else res.data
        assert items == []


# ---------------------------------------------------------------------------
# for-object endpoint
# ---------------------------------------------------------------------------


class TestForObjectEndpoint:
    def test_returns_signatures_for_target(
        self, api_client, signer_user, project_a, project_b
    ):
        Signature.objects.create(
            signer=signer_user, title="A1", content_hash=_hash("A1"), content_object=project_a
        )
        Signature.objects.create(
            signer=signer_user, title="A2", content_hash=_hash("A2"), content_object=project_a
        )
        Signature.objects.create(
            signer=signer_user, title="B1", content_hash=_hash("B1"), content_object=project_b
        )
        api_client.force_authenticate(user=signer_user)
        res = api_client.get(
            f"/api/v1/signatures/for-object/?content_type_label=core.project&object_id={project_a.id}"
        )
        assert res.status_code == 200
        assert res.data["count"] == 2
        assert res.data["object_id"] == project_a.id
        assert res.data["content_type_label"] == "core.project"
        titles = {s["title"] for s in res.data["signatures"]}
        assert titles == {"A1", "A2"}

    def test_missing_params_returns_400(self, api_client, signer_user):
        api_client.force_authenticate(user=signer_user)
        r = api_client.get("/api/v1/signatures/for-object/")
        assert r.status_code == 400

    def test_malformed_label_returns_400(self, api_client, signer_user):
        api_client.force_authenticate(user=signer_user)
        r = api_client.get(
            "/api/v1/signatures/for-object/?content_type_label=noprefix&object_id=1"
        )
        assert r.status_code == 400

    def test_unknown_content_type_returns_404(self, api_client, signer_user):
        api_client.force_authenticate(user=signer_user)
        r = api_client.get(
            "/api/v1/signatures/for-object/?content_type_label=core.nope&object_id=1"
        )
        assert r.status_code == 404

    def test_non_integer_object_id_returns_400(self, api_client, signer_user):
        api_client.force_authenticate(user=signer_user)
        r = api_client.get(
            "/api/v1/signatures/for-object/?content_type_label=core.project&object_id=abc"
        )
        assert r.status_code == 400

    def test_endpoint_requires_auth(self, api_client, project_a):
        r = api_client.get(
            f"/api/v1/signatures/for-object/?content_type_label=core.project&object_id={project_a.id}"
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Create with GFK over the wire
# ---------------------------------------------------------------------------


class TestCreateWithGFK:
    def test_post_with_content_type_and_object_id(self, api_client, signer_user, project_a):
        ct = ContentType.objects.get_for_model(Project)
        api_client.force_authenticate(user=signer_user)
        res = api_client.post(
            "/api/v1/signatures/",
            {
                "title": "Inline GFK",
                "hash_alg": "sha256",
                "content_hash": _hash("payload"),
                "content_type": ct.id,
                "object_id": project_a.id,
            },
            format="json",
        )
        assert res.status_code == 201
        sig = Signature.objects.get(pk=res.data["id"])
        assert sig.content_object == project_a
        assert res.data["content_type_label"] == "core.project"
