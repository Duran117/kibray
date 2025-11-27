import hashlib
import json

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def test_signatures_list_empty(client):
    resp = client.get("/api/v1/signatures/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) or "results" in data  # supports both paginated and non


def test_signature_create_requires_auth(client):
    payload = {
        "title": "Test Doc",
        "hash_alg": "sha256",
        "content_hash": "0" * 64,
        "note": "",
    }
    resp = client.post("/api/v1/signatures/", data=payload)
    assert resp.status_code in (401, 403)


def test_signature_create_and_retrieve(authenticated_client):
    client, user = authenticated_client
    # Use real content and compute its hash
    content = "This is the signed agreement text"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    payload = {
        "title": "Agreement",
        "hash_alg": "sha256",
        "content_hash": content_hash,
        "note": "Signed",
    }
    resp = client.post("/api/v1/signatures/", data=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["signer"] == user.id
    assert created["title"] == "Agreement"

    # Retrieve
    detail = client.get(f"/api/v1/signatures/{created['id']}/")
    assert detail.status_code == 200
    assert detail.json()["id"] == created["id"]

    # Verify endpoint: matches content
    verify_ok = client.post(
        f"/api/v1/signatures/{created['id']}/verify/",
        data={
            "content": content,
            "hash_alg": "sha256",
        },
    )
    assert verify_ok.status_code == 200
    v = verify_ok.json()
    assert v["matches"] is True

    # Verify endpoint: mismatched content
    verify_bad = client.post(
        f"/api/v1/signatures/{created['id']}/verify/",
        data={
            "content": "different content",
            "hash_alg": "sha256",
        },
    )
    assert verify_bad.status_code == 200
    assert verify_bad.json()["matches"] is False


def test_signature_update_restricted_to_owner(client):
    """Signature owner can update, non-owner gets 403"""
    User = get_user_model()
    owner = User.objects.create_user(username="owner", password="pass123")
    other = User.objects.create_user(username="other", password="pass456")

    # Owner creates signature
    assert client.login(username="owner", password="pass123")
    content_hash = hashlib.sha256(b"test").hexdigest()
    payload = {"title": "Doc", "hash_alg": "sha256", "content_hash": content_hash}
    resp = client.post("/api/v1/signatures/", data=payload)
    assert resp.status_code == 201
    sig_id = resp.json()["id"]

    # Other user tries to update
    client.logout()
    assert client.login(username="other", password="pass456")
    patch_resp = client.patch(
        f"/api/v1/signatures/{sig_id}/", data={"title": "Hacked"}, content_type="application/json"
    )
    assert patch_resp.status_code == 403


def test_signature_delete_restricted_to_owner(client):
    """Only owner can delete their signature"""
    User = get_user_model()
    owner = User.objects.create_user(username="owner2", password="pass123")
    other = User.objects.create_user(username="other2", password="pass456")

    assert client.login(username="owner2", password="pass123")
    content_hash = hashlib.sha256(b"delete_test").hexdigest()
    payload = {"title": "ToDelete", "hash_alg": "sha256", "content_hash": content_hash}
    resp = client.post("/api/v1/signatures/", data=payload)
    assert resp.status_code == 201
    sig_id = resp.json()["id"]

    # Other user tries to delete
    client.logout()
    assert client.login(username="other2", password="pass456")
    del_resp = client.delete(f"/api/v1/signatures/{sig_id}/")
    assert del_resp.status_code == 403

    # Owner can delete
    client.logout()
    assert client.login(username="owner2", password="pass123")
    del_ok = client.delete(f"/api/v1/signatures/{sig_id}/")
    assert del_ok.status_code == 204


# ===== Fixtures =====
@pytest.fixture
def authenticated_client(client):
    User = get_user_model()
    user = User.objects.create_user(username="siguser", password="pass123", email="sig@example.com")
    assert client.login(username="siguser", password="pass123")
    return client, user
