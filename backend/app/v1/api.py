"""
filename: api.py
author: Tu Nombre
date: 2026-05-13
version: 1.0
description: Agrupa todos los routers de la versión 1 de la API.
"""
from fastapi import APIRouter
from .routers import auth, profile, artists, tracks, history, etl

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(artists.router, prefix="/artists", tags=["artists"])
router.include_router(tracks.router, prefix="/tracks", tags=["tracks"])
router.include_router(history.router, prefix="/history", tags=["history"])
router.include_router(etl.router, prefix="/etl", tags=["etl"])