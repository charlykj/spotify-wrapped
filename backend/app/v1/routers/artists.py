from fastapi import APIRouter, Depends
from app.v1.dependencies import get_current_user
from app.v1.services.artists_service import get_top_artists_from_db

router = APIRouter()

@router.get("/top")
def top_artists(spotify_id: str = Depends(get_current_user)):
    return get_top_artists_from_db(spotify_id)