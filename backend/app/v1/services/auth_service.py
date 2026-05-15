import base64, hashlib, os
from datetime import datetime, timedelta, timezone
import psycopg2, requests
from jose import jwt
from app.core.config import settings

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "user-read-private user-read-email user-top-read user-read-recently-played"

def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge

def build_spotify_auth_url(challenge, state):
    import urllib.parse
    params = {"client_id": settings.SPOTIFY_CLIENT_ID, "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI, "code_challenge_method": "S256",
        "code_challenge": challenge, "state": state, "scope": SCOPES}
    return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

def _get_conn():
    return psycopg2.connect(settings.DATABASE_URL)

def save_pkce_session(state, verifier):
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO public.pkce_sessions (state, verifier) VALUES (%s, %s) ON CONFLICT (state) DO NOTHING", (state, verifier))
    conn.commit()
    cur.close()
    conn.close()
    print(f"[PKCE] Guardado state={state}")

def pop_pkce_session(state):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT verifier FROM public.pkce_sessions WHERE state = %s", (state,))
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM public.pkce_sessions WHERE state = %s", (state,))
                conn.commit()
                return row[0]
    return None

def exchange_code_for_tokens(code, verifier):
    r = requests.post(SPOTIFY_TOKEN_URL, data={"grant_type": "authorization_code",
        "code": code, "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID, "code_verifier": verifier},
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    r.raise_for_status()
    return r.json()

def refresh_spotify_token(refresh_token):
    r = requests.post(SPOTIFY_TOKEN_URL, data={"grant_type": "refresh_token",
        "refresh_token": refresh_token, "client_id": settings.SPOTIFY_CLIENT_ID},
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    r.raise_for_status()
    return r.json()

def upsert_user(spotify_profile, token_data):
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO dwh.dim_users
                (spotify_id, display_name, email, country, followers, product,
                 spotify_access_token, spotify_refresh_token, token_expires_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (spotify_id) DO UPDATE SET
                display_name=EXCLUDED.display_name, email=EXCLUDED.email,
                country=EXCLUDED.country, followers=EXCLUDED.followers,
                product=EXCLUDED.product, spotify_access_token=EXCLUDED.spotify_access_token,
                spotify_refresh_token=EXCLUDED.spotify_refresh_token,
                token_expires_at=EXCLUDED.token_expires_at""",
                (spotify_profile["id"], spotify_profile.get("display_name"),
                 spotify_profile.get("email"), spotify_profile.get("country"),
                 spotify_profile.get("followers",{}).get("total"),
                 spotify_profile.get("product"), token_data["access_token"],
                 token_data.get("refresh_token"), expires_at))
        conn.commit()

def create_app_jwt(spotify_id):
    payload = {"sub": spotify_id, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def get_valid_spotify_token(spotify_id):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT spotify_access_token, spotify_refresh_token, token_expires_at FROM dwh.dim_users WHERE spotify_id = %s", (spotify_id,))
            row = cur.fetchone()
    if not row:
        raise ValueError(f"Usuario {spotify_id} no encontrado.")
    access_token, refresh_token, expires_at = row
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at - now < timedelta(minutes=5):
        new_tokens = refresh_spotify_token(refresh_token)
        new_expires = now + timedelta(seconds=new_tokens.get("expires_in", 3600))
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE dwh.dim_users SET spotify_access_token=%s, token_expires_at=%s WHERE spotify_id=%s",
                    (new_tokens["access_token"], new_expires, spotify_id))
            conn.commit()
        return new_tokens["access_token"]
    return access_token