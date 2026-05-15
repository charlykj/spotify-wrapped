# Configuración Inicial

## Qué se configuró / implementó

Se configuró el entorno de desarrollo completo: cuenta de Spotify Developer, base de datos PostgreSQL en Neon, entorno virtual de Python y variables de entorno.

## Pasos realizados

1. Se creó una app en Spotify Developer Dashboard con el nombre "My Spotify Wrapped"
2. Se configuró el Redirect URI: `http://127.0.0.1:8000/v1/auth/callback`
3. Se creó el proyecto `spotify-dwh` en Neon (PostgreSQL serverless)
4. Se configuró el archivo `.env` con las credenciales
5. Se creó el entorno virtual con `python3 -m venv venv`
6. Se instalaron las dependencias con `pip install`
7. Se corrió `alembic upgrade head` para crear las tablas

## Screenshots

[Insertar captura del Spotify Developer Dashboard]
[Insertar captura del proyecto en Neon]

## Prompt utilizado

No se utilizó ninguna técnica de IA.

## Técnica de prompting aplicada

No aplica.