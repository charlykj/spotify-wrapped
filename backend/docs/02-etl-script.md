# ETL Pipeline — Implementación

## Qué se configuró / implementó

Se implementó el pipeline ETL completo con 3 fases separadas (Extract, Transform, Load) para los 4 endpoints de Spotify. Cada fase está en funciones independientes con docstrings.

## Endpoints consumidos

| Endpoint Spotify | Tabla DWH |
|---|---|
| `GET /v1/me` | `dwh.dim_users` |
| `GET /v1/me/top/artists` | `dwh.dim_artists` |
| `GET /v1/me/top/tracks` | `dwh.dim_tracks` |
| `GET /v1/me/player/recently-played` | `dwh.fact_listening_history` |

## Fases del ETL

### Extract
Cada función `extract_*` llama al endpoint de Spotify y retorna los datos crudos en formato JSON.

### Transform
Cada función `transform_*` normaliza los datos crudos al modelo dimensional, extrayendo solo los campos necesarios.

### Load
Cada función `load_*` inserta los datos en PostgreSQL usando `ON CONFLICT DO NOTHING` para garantizar idempotencia.

## Carga incremental

El ETL usa `cursor_next_ms` de `etl_audit` para traer solo las reproducciones nuevas desde la última ejecución exitosa.

## Auditoría

Cada ejecución queda registrada en `dwh.etl_audit` con: fecha inicio, fecha fin, duración en ms, registros nuevos por tabla y cursor para la próxima ejecución.

## Screenshots

[Insertar captura del resultado del ETL en Swagger]
[Insertar captura de etl_audit en Neon]

## Prompt utilizado

No se utilizó ninguna técnica de IA.

## Técnica de prompting aplicada

No aplica.