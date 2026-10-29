"""Verify Managed Better Auth JWTs (EdDSA) against Neon JWKS."""
from __future__ import annotations

import base64
import os
import time
from urllib.parse import urlparse

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jwt import PyJWTError

_JWKS_CACHE: dict = {"at": 0.0, "keys": None, "origin": "", "jwks_url": ""}


def _auth_origin(base_url: str) -> str:
    parsed = urlparse(base_url.rstrip("/"))
    return f"{parsed.scheme}://{parsed.netloc}"


def _jwks_url(base_url: str) -> str:
    explicit = os.getenv("NEON_AUTH_JWKS_URL", "").strip()
    if explicit:
        return explicit
    return base_url.rstrip("/") + "/.well-known/jwks.json"


def _load_jwks(jwks_url: str) -> dict:
    now = time.time()
    if _JWKS_CACHE["keys"] is not None and _JWKS_CACHE["jwks_url"] == jwks_url and _JWKS_CACHE["at"] > now - 3600:
        return _JWKS_CACHE["keys"]
    r = httpx.get(jwks_url, timeout=10, follow_redirects=False)
    r.raise_for_status()
    data = r.json()
    _JWKS_CACHE.update({"at": now, "keys": data, "jwks_url": jwks_url})
    return data


def _b64url(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * ((4 - len(data) % 4) % 4))


def _signing_key(token: str, jwks: dict):
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid and jwk.get("kty") == "OKP":
            return Ed25519PublicKey.from_public_bytes(_b64url(jwk["x"]))
    raise ValueError("Matching JWK not found")


def validate_neon_token(token: str, base_url: str) -> dict | None:
    if not token or not base_url:
        return None
    origin = _auth_origin(base_url)
    try:
        jwks = _load_jwks(_jwks_url(base_url))
        key = _signing_key(token, jwks)
        payload = jwt.decode(
            token,
            key=key,
            algorithms=["EdDSA"],
            issuer=origin,
            audience=origin,
        )
        return payload
    except (PyJWTError, ValueError, httpx.HTTPError):
        return None
