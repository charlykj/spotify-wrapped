import requests
from fastapi import HTTPException, status

SPOTIFY_API_BASE = "https://api.spotify.com/v1"

def spotify_get(endpoint: str, token: str, params: dict = None) -> dict:
    url = f"{SPOTIFY_API_BASE}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params or {})
    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Spotify invalido o expirado.")
    if response.status_code == 403:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos suficientes en Spotify.")
    response.raise_for_status()
    return response.json()