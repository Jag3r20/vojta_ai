from pathlib import Path

import msal
from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Single-user app: the flow dict only needs to survive between the redirect
# to Microsoft and the callback hitting this same process.
_pending_flow: dict | None = None


class GraphAuthError(Exception):
    pass


#  MSAL requests these automatically and rejects them if passed explicitly.
_MSAL_RESERVED_SCOPES = {"openid", "profile", "offline_access"}


def _scopes() -> list[str]:
    return [s for s in settings.graph_scopes.split() if s not in _MSAL_RESERVED_SCOPES]


def _token_cache_path() -> Path:
    return Path(settings.data_dir) / "token_cache.bin"


def _fernet() -> Fernet:
    return Fernet(settings.token_encryption_key.encode())


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    path = _token_cache_path()
    if path.exists():
        cache.deserialize(_fernet().decrypt(path.read_bytes()).decode())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if not cache.has_state_changed:
        return
    path = _token_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fernet().encrypt(cache.serialize().encode()))


def _require_configured() -> None:
    if not (settings.tenant_id and settings.client_id and settings.client_secret):
        raise HTTPException(
            status_code=500,
            detail=(
                "graph-tools není nastavený pro přihlášení k Microsoftu - "
                "chybí TENANT_ID/CLIENT_ID/CLIENT_SECRET v .env "
                "(viz docs/entra-setup.md)"
            ),
        )


def _build_msal_app(cache: msal.SerializableTokenCache | None = None) -> msal.ConfidentialClientApplication:
    _require_configured()
    return msal.ConfidentialClientApplication(
        client_id=settings.client_id,
        client_credential=settings.client_secret,
        authority=f"https://login.microsoftonline.com/{settings.tenant_id}",
        token_cache=cache,
    )


def get_graph_access_token() -> str:
    """Used by Excel/OneNote modules to get a valid access token for Graph calls."""
    cache = _load_cache()
    app = _build_msal_app(cache)
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(_scopes(), account=accounts[0])
    _save_cache(cache)
    if not result:
        raise GraphAuthError("Přihlášení k Microsoftu vypršelo, otevři /auth/login")
    return result["access_token"]


@router.get("/login")
def login() -> RedirectResponse:
    global _pending_flow
    app = _build_msal_app()
    flow = app.initiate_auth_code_flow(scopes=_scopes(), redirect_uri=settings.graph_redirect_uri)
    _pending_flow = flow
    return RedirectResponse(flow["auth_uri"])


@router.get("/callback")
def callback(request: Request) -> HTMLResponse:
    global _pending_flow
    if _pending_flow is None:
        raise HTTPException(
            status_code=400,
            detail="Přihlašovací relace vypršela nebo nebyla zahájena, zkus to znovu na /auth/login",
        )
    flow, _pending_flow = _pending_flow, None

    cache = _load_cache()
    app = _build_msal_app(cache)
    result = app.acquire_token_by_auth_code_flow(flow, dict(request.query_params))
    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=f"Přihlášení k Microsoftu selhalo: {result.get('error_description', result['error'])}",
        )
    _save_cache(cache)
    return HTMLResponse("<h1>Přihlášeno</h1><p>Teď můžeš toto okno zavřít.</p>")


@router.get("/status")
def status() -> dict:
    cache = _load_cache()
    app = _build_msal_app(cache)
    accounts = app.get_accounts()
    if not accounts:
        return {"logged_in": False}
    result = app.acquire_token_silent(_scopes(), account=accounts[0])
    _save_cache(cache)
    return {"logged_in": result is not None, "account": accounts[0].get("username")}
