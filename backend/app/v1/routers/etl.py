from fastapi import APIRouter, Depends, HTTPException, status
from app.v1.dependencies import get_current_user
from app.v1.services.etl_service import get_etl_status, run_etl

router = APIRouter()

@router.post("/run")
def trigger_etl(spotify_id: str = Depends(get_current_user)):
    try:
        return run_etl(spotify_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en el pipeline ETL: {str(exc)}")

@router.get("/status")
def etl_status(spotify_id: str = Depends(get_current_user)):
    return get_etl_status(spotify_id)