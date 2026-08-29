import uuid

import pytest
from fastapi.testclient import TestClient
from jose import JWTError, jwt

from app.auth_utils import create_access_token, decode_access_token
from app.config import settings
from app.main import app
from app.schemas.user import UserCreate


def test_access_token_contains_and_validates_security_claims():
    subject = str(uuid.uuid4())
    token = create_access_token({"sub": subject, "role": "sender"})

    payload = decode_access_token(token)

    assert payload["sub"] == subject
    assert payload["role"] == "sender"
    assert payload["iss"] == settings.jwt_issuer
    assert payload["aud"] == settings.jwt_audience
    assert {"iat", "nbf", "exp"}.issubset(payload)


def test_access_token_rejects_wrong_audience():
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": settings.jwt_issuer,
            "aud": "wrong-client",
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(JWTError):
        decode_access_token(token)


def test_root_response_sets_browser_security_headers():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_registration_schema_rejects_unknown_fields_and_short_password():
    with pytest.raises(ValueError):
        UserCreate(
            name="Test",
            phone="09123456789",
            password="short",
            untrusted_admin_flag=True,
        )
