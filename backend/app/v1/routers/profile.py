from fastapi import APIRouter, Depends, HTTPException
from app.v1.dependencies import get_current_user
from app.v1.services.profile_service import get_profile

router = APIRouter()

@router.get("/me")
def profile_me(spotify_id: str = Depends(get_current_user)):
    profile = get_profile(spotify_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")
    return profile