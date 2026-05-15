"""
filename: config.py
author: Tu Nombre
date: 2026-05-13
version: 1.0
description: Configuración central de la app usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: str
    DATABASE_URL: str
    APP_NAME: str = "Spotify DWH API"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str
    FRONTEND_URL: str

    class Config:
        env_file = ".env"

settings = Settings()