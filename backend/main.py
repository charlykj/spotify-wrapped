"""
filename: main.py
author: Tu Nombre
date: 2026-05-13
version: 1.0
description: Entry point de la API FastAPI para Spotify DWH.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.v1.api import router as v1_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/v1")