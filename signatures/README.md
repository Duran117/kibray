# Signatures App

A minimal, isolated app to store digital signatures linked to users.

## Model
- `Signature`: signer (FK to `AUTH_USER_MODEL`), title, signed_at, hash_alg, content_hash, note, optional file.

## API
Base path: `/api/v1/signatures/`
- `GET /` list
- `POST /` create (assigns signer = request.user)
- `GET /{id}/` retrieve
- `PATCH /{id}/` update (owner-only)
- `DELETE /{id}/` delete (owner-only)
- `POST /{id}/verify` verify provided content against stored hash

## Permissions
- Read: public
- Modify: owner-only (`IsOwnerOrReadOnly`)

## Tests
See `tests/test_signatures_api.py`.