from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import secrets
from app.core.spotify_client import spotify_get
from app.v1.services.auth_service import (
    build_spotify_auth_url, generate_pkce_pair,
    save_pkce_session, pop_pkce_session,
    exchange_code_for_tokens, upsert_user, create_app_jwt
)
from app.core.config import settings

router = APIRouter()

@router.get("/login")
def login():
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    save_pkce_session(state, verifier)
    url = build_spotify_auth_url(challenge, state)
    return RedirectResponse(url)

@router.get("/callback")
def callback(code: str, state: str):
    verifier = pop_pkce_session(state)
    if not verifier:
        raise HTTPException(status_code=400, detail="State invalido o expirado.")
    token_data = exchange_code_for_tokens(code, verifier)
    profile = spotify_get("/me", token_data["access_token"])
    upsert_user(profile, token_data)
    jwt = create_app_jwt(profile["id"])
    return RedirectResponse(f"{settings.FRONTEND_URL}/callback?token={jwt}")
