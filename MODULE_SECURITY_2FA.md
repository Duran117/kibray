# Security: Two-Factor Authentication (2FA) with TOTP

This module adds optional TOTP-based 2FA to user accounts without external dependencies.

## Overview
- Standard TOTP (RFC 6238), 6 digits, 30s step.
- App-agnostic (Google Authenticator, 1Password, Authy, etc.).
- Enforced at JWT login when enabled for a user.

## Models
- `TwoFactorProfile(user, secret_base32, enabled)`
  - Methods: `generate_totp()`, `verify_totp(code, drift=1)`, `otpauth_uri(issuer)`.

## API Endpoints
Base path: `/api/v1/2fa/`

- POST `setup/` (auth required)
  - Response: `{ secret, otpauth_uri }`
- POST `enable/` (auth required)
  - Body: `{ code: "123456" }`
  - Response: `{ enabled: true }`
- POST `disable/` (auth required)
  - Body: `{ code: "123456" }` (optional if implemented)
  - Response: `{ enabled: false }`

## Login with 2FA (JWT)
Replace default login with `TwoFactorTokenObtainPair` at `/api/v1/auth/login/`.

- If user has 2FA enabled:
  - Request must include `otp_code`:
  ```json
  { "username": "alice", "password": "pass", "otp_code": "123456" }
  ```
  - If TOTP valid: returns access/refresh tokens.
  - If invalid/missing: 401 with error.
- If user does not have 2FA enabled: normal username/password works.

## Error Codes
- 401 invalid credentials or OTP.
- 400 malformed payload.

## Notes
- Clock drift: allowed ±1 step by default.
- Recovery codes: not yet implemented (future work).
- Rate limiting: consider adding at the ingress layer.
