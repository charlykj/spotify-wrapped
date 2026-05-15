from fastapi import APIRouter, Depends
from app.v1.dependencies import get_current_user
from app.v1.services.history_service import get_recently_played_from_db

router = APIRouter()

@router.get("/recently-played")
def recently_played(spotify_id: str = Depends(get_current_user)):
    return get_recently_played_from_db(spotify_id)