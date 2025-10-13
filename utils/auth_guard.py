"""
FastAPI dependency for verifying Authorization bearer tokens in agent endpoints.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Dict, Optional

import httpx
from fastapi import Header, HTTPException, status
from jose import JWTError, jwt
from jose.utils import base64url_decode

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Shared cache for JWKS retrieval.
_JWKS_CACHE: Dict[str, Dict[str, bytes]] = {}
_JWKS_LOCK = asyncio.Lock()


class AuthConfigError(RuntimeError):
    """Raised when secure mode is requested but configuration is incomplete."""


def _missing_bearer() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing bearer",
    )


def _load_auth_config() -> Dict[str, Optional[str]]:
    mode = os.getenv("AUTH_MODE", "SECURE").upper()
    return {
        "mode": mode,
        "issuer": os.getenv("AUTH_ISS"),
        "audience": os.getenv("AUTH_AUD"),
        "jwks_path": os.getenv("AUTH_JWKS_PATH"),
        "jwks_url": os.getenv("AUTH_JWKS_URL"),
    }


def _jwk_to_pem(key_dict: Dict[str, str]) -> bytes:
    """Convert an RSA JWK to PEM-encoded public key bytes."""
    if key_dict.get("kty") != "RSA":
        raise AuthConfigError("Only RSA JWKs supported")
    n_bytes = base64url_decode(key_dict["n"].encode("utf-8"))
    e_bytes = base64url_decode(key_dict["e"].encode("utf-8"))
    n_int = int.from_bytes(n_bytes, "big")
    e_int = int.from_bytes(e_bytes, "big")
    public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
    public_key = public_numbers.public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


async def _load_jwks(source: str, *, from_path: bool) -> Dict[str, bytes]:
    """Load JWKS once and cache PEM-encoded public keys keyed by kid."""
    async with _JWKS_LOCK:
        if source in _JWKS_CACHE:
            return _JWKS_CACHE[source]

        if from_path:
            with open(source, "r", encoding="utf-8") as fh:
                jwks = json.load(fh)
        else:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(source)
            if response.status_code != 200:
                raise AuthConfigError(f"Failed to fetch JWKS ({response.status_code})")
            jwks = response.json()

        keys = jwks.get("keys", [])
        if not keys:
            raise AuthConfigError("JWKS does not contain keys")

        pem_map = {}
        for entry in keys:
            kid = entry.get("kid") or "default"
            pem_map[kid] = _jwk_to_pem(entry)
        _JWKS_CACHE[source] = pem_map
        return pem_map


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise _missing_bearer()
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise _missing_bearer()
    return parts[1]


async def _decode_token(
    token: str,
    *,
    issuer: Optional[str],
    audience: Optional[str],
    jwks_path: Optional[str],
    jwks_url: Optional[str],
    verify_exp: bool,
) -> Dict[str, object]:
    """
    Decode a JWT applying RS256 signature validation.

    verify_exp toggles whether the expiration claim is enforced.
    """
    if not issuer or not audience or not (jwks_path or jwks_url):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="auth configuration incomplete",
        )

    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token header")

    if header.get("alg") != "RS256":
        raise HTTPException(status_code=401, detail="invalid alg")

    kid = header.get("kid") or "default"
    source = jwks_path or jwks_url
    try:
        keys = await _load_jwks(source, from_path=bool(jwks_path))
    except AuthConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    key = keys.get(kid)
    if key is None:
        if len(keys) == 1:
            key = next(iter(keys.values()))
        else:
            raise HTTPException(status_code=401, detail="unknown kid")

    options = {"leeway": 30, "verify_exp": verify_exp}
    try:
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
            options=options,
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"verification failed: {exc}")


async def auth_guard(authorization: Optional[str] = Header(default=None)) -> Dict[str, object]:
    """
    FastAPI dependency: returns decoded JWT claims or raises HTTPException(401).

    In vulnerable mode (AUTH_MODE=VULN), only the presence of the header is
    enforced; no JWT validation is performed to emulate a bypass.
    """
    token = _extract_token(authorization)
    config = _load_auth_config()

    if config["mode"] == "VULN":
        return {"vuln": True, "token": token}

    if config["mode"] != "SECURE":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="unsupported auth mode",
        )

    return await _decode_token(
        token,
        issuer=config["issuer"],
        audience=config["audience"],
        jwks_path=config["jwks_path"],
        jwks_url=config["jwks_url"],
        verify_exp=True,
    )


# Example FastAPI usage:
# @app.post("/jsonrpc")
# async def jsonrpc(..., claims=Depends(auth_guard)):
#     # protected behavior
#     return {"claims": claims}
