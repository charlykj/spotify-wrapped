from fastapi import APIRouter, Depends
from app.v1.dependencies import get_current_user
from app.v1.services.tracks_service import get_top_tracks_from_db

router = APIRouter()

@router.get("/top")
def top_tracks(spotify_id: str = Depends(get_current_user)):
    return get_top_tracks_from_db(spotify_id)