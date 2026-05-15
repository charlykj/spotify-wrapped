# DDL — Migraciones del DWH

## Qué se configuró / implementó

Se creó el schema `dwh` en PostgreSQL (Neon) con 5 tablas que forman el modelo dimensional star schema. Las migraciones se manejan con Alembic.

## Script DDL completo

```sql
-- Schema principal
CREATE SCHEMA IF NOT EXISTS dwh;

-- Tabla de sesiones PKCE para el flujo OAuth
CREATE TABLE IF NOT EXISTS public.pkce_sessions (
    state      VARCHAR(128) PRIMARY KEY,
    verifier   TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimensión usuarios
CREATE TABLE IF NOT EXISTS dwh.dim_users (
    user_id               SERIAL PRIMARY KEY,
    spotify_id            VARCHAR(100) UNIQUE NOT NULL,
    display_name          VARCHAR(255),
    email                 VARCHAR(255),
    country               VARCHAR(10),
    followers             INT,
    product               VARCHAR(20),
    spotify_access_token  TEXT,
    spotify_refresh_token TEXT,
    token_expires_at      TIMESTAMP,
    loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimensión artistas
CREATE TABLE IF NOT EXISTS dwh.dim_artists (
    artist_id       SERIAL PRIMARY KEY,
    spotify_id      VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    popularity      INT,
    followers_count INT,
    genres          TEXT[],
    loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimensión tracks
CREATE TABLE IF NOT EXISTS dwh.dim_tracks (
    track_id     SERIAL PRIMARY KEY,
    spotify_id   VARCHAR(100) UNIQUE NOT NULL,
    name         VARCHAR(255) NOT NULL,
    artist_id    INT REFERENCES dwh.dim_artists(artist_id),
    album_name   VARCHAR(255),
    duration_ms  INT,
    popularity   INT,
    explicit     BOOLEAN,
    loaded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de hechos: historial de reproducción
CREATE TABLE IF NOT EXISTS dwh.fact_listening_history (
    id           SERIAL PRIMARY KEY,
    user_id      INT NOT NULL REFERENCES dwh.dim_users(user_id),
    track_id     INT NOT NULL REFERENCES dwh.dim_tracks(track_id),
    artist_id    INT NOT NULL REFERENCES dwh.dim_artists(artist_id),
    played_at    TIMESTAMP NOT NULL,
    hour_of_day  INT,
    day_of_week  VARCHAR(10),
    context_type VARCHAR(50),
    UNIQUE (user_id, played_at)
);

-- Tabla de auditoría ETL
CREATE TABLE IF NOT EXISTS dwh.etl_audit (
    audit_id         SERIAL PRIMARY KEY,
    spotify_user_id  VARCHAR(100) NOT NULL,
    started_at       TIMESTAMP NOT NULL,
    finished_at      TIMESTAMP,
    duration_ms      INT,
    status           VARCHAR(20) NOT NULL,
    error_message    TEXT,
    users_new        INT DEFAULT 0,
    artists_new      INT DEFAULT 0,
    artists_skipped  INT DEFAULT 0,
    tracks_new       INT DEFAULT 0,
    tracks_skipped   INT DEFAULT 0,
    history_new      INT DEFAULT 0,
    history_skipped  INT DEFAULT 0,
    cursor_after_ms  BIGINT,
    cursor_next_ms   BIGINT
);
```

## Screenshots

[Insertar captura de pantalla de las tablas creadas en Neon]

## Prompt utilizado

No se utilizó ninguna técnica de IA.

## Técnica de prompting aplicada

No aplica.