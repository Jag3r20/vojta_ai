from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app import auth as auth_module
from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def reset_pending_flow():
    auth_module._pending_flow = None
    yield
    auth_module._pending_flow = None


@pytest.fixture
def mock_app():
    """Mocked msal.ConfidentialClientApplication instance for a test."""
    instance = MagicMock()
    instance.get_accounts.return_value = []
    with patch("app.auth.msal.ConfidentialClientApplication", return_value=instance):
        yield instance


@pytest.fixture
def client(tmp_path, monkeypatch, mock_app):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode())
    monkeypatch.setattr(settings, "tenant_id", "test-tenant")
    monkeypatch.setattr(settings, "client_id", "test-client")
    monkeypatch.setattr(settings, "client_secret", "test-secret")
    monkeypatch.setattr(settings, "graph_redirect_uri", "http://localhost:8000/auth/callback")
    monkeypatch.setattr(settings, "graph_scopes", "User.Read offline_access")
    return TestClient(app)


def test_status_logged_out_when_no_cache(client):
    response = client.get("/auth/status")
    assert response.status_code == 200
    assert response.json() == {"logged_in": False}


def test_login_redirects_to_microsoft(client, mock_app):
    mock_app.initiate_auth_code_flow.return_value = {
        "state": "abc123",
        "auth_uri": "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/authorize?state=abc123",
    }

    response = client.get("/auth/login", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == (
        "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/authorize?state=abc123"
    )
    mock_app.initiate_auth_code_flow.assert_called_once_with(
        scopes=["User.Read", "offline_access"],
        redirect_uri="http://localhost:8000/auth/callback",
    )


def test_callback_without_prior_login_returns_400(client):
    response = client.get("/auth/callback?code=xyz&state=abc123")
    assert response.status_code == 400


def test_callback_rejects_error_response_from_microsoft(client, mock_app):
    mock_app.initiate_auth_code_flow.return_value = {
        "state": "abc123",
        "auth_uri": "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/authorize?state=abc123",
    }
    mock_app.acquire_token_by_auth_code_flow.return_value = {
        "error": "access_denied",
        "error_description": "uživatel odmítl souhlas",
    }

    client.get("/auth/login", follow_redirects=False)
    response = client.get("/auth/callback?code=xyz&state=abc123")

    assert response.status_code == 400


def test_callback_success_saves_encrypted_cache_and_status_reports_logged_in(client, mock_app, tmp_path):
    mock_cache = MagicMock()
    mock_cache.has_state_changed = True
    mock_cache.serialize.return_value = '{"access_token": "fake-token", "secret": true}'

    mock_app.initiate_auth_code_flow.return_value = {
        "state": "abc123",
        "auth_uri": "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/authorize?state=abc123",
    }
    mock_app.acquire_token_by_auth_code_flow.return_value = {"access_token": "fake-token"}

    with patch("app.auth.msal.SerializableTokenCache", return_value=mock_cache):
        client.get("/auth/login", follow_redirects=False)
        response = client.get("/auth/callback?code=xyz&state=abc123")

    assert response.status_code == 200
    cache_file = tmp_path / "token_cache.bin"
    assert cache_file.exists()
    # the cache on disk must be encrypted, not plaintext MSAL state
    assert b"access_token" not in cache_file.read_bytes()

    mock_app.get_accounts.return_value = [{"username": "filip@example.com"}]
    mock_app.acquire_token_silent.return_value = {"access_token": "fake-token"}

    response = client.get("/auth/status")

    assert response.status_code == 200
    assert response.json() == {"logged_in": True, "account": "filip@example.com"}
