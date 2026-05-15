# Respuestas Técnicas — Carlos Camargo

**Fecha:** 2026-05-14

---

## Pregunta 1 — Granularidad de fact_listening_history

La granularidad de `fact_listening_history` es una reproducción de un track por un usuario en un momento específico. Es decir, una fila representa exactamente una vez que el usuario escuchó una canción en un instante determinado.

`played_at` no puede ser clave primaria por sí sola porque es posible que dos usuarios diferentes escuchen música exactamente al mismo instante, generando timestamps idénticos pero para usuarios distintos. Por eso la constraint de idempotencia es `UNIQUE (user_id, played_at)`: la combinación de usuario y momento garantiza unicidad. Un mismo usuario no puede tener dos reproducciones en el exactamente mismo milisegundo.

---

## Pregunta 2 — ON CONFLICT DO NOTHING

`ON CONFLICT (spotify_id) DO NOTHING` en las dimensiones garantiza **idempotencia**: si un registro ya existe, la inserción se ignora sin error. `ON CONFLICT (user_id, played_at) DO NOTHING` en la tabla de hechos garantiza que no se dupliquen reproducciones.

Si no existiera esa cláusula y se corriera el ETL dos veces el mismo día, se intentaría insertar los mismos registros dos veces y la base de datos lanzaría errores de violación de restricción de unicidad, rompiendo el pipeline.

---

## Pregunta 3 — FK entre dimensiones

`dim_tracks` tiene una FK hacia `dim_artists` (`artist_id`). Esa relación entre dimensiones genera un **snowflake schema**, porque `dim_tracks` no es completamente plana sino que depende de otra dimensión.

La alternativa en un star schema puro sería desnormalizar `artist_name` directamente dentro de `dim_tracks`, eliminando la FK. Se decidió mantener la FK porque simplifica el ETL (no hay que duplicar datos del artista) y las queries analíticas siguen siendo simples con un solo JOIN adicional. El trade-off es que se pierde la pureza del star schema.

---

## Pregunta 4 — Flujo OAuth PKCE

1. El usuario hace clic en "Conectar con Spotify"
2. El backend genera un par `(code_verifier, code_challenge)` con SHA-256
3. Guarda el `state` y el `verifier` en `public.pkce_sessions`
4. Redirige al usuario a `accounts.spotify.com` con el `code_challenge` y el `state`
5. El usuario autoriza la app en Spotify
6. Spotify redirige al callback del backend con un `code` y el mismo `state`
7. El backend recupera el `verifier` usando el `state`, lo elimina de la DB
8. Intercambia el `code` + `verifier` por `access_token` y `refresh_token`
9. Crea un JWT propio firmado con `SECRET_KEY` y redirige al frontend con `?token=JWT`
10. El frontend guarda el JWT en `localStorage`

PKCE (Proof Key for Code Exchange) se usa para proteger el flujo OAuth en apps públicas donde no se puede guardar un `client_secret` de forma segura. Evita que un atacante intercepte el `code` y lo use, porque sin el `verifier` original no puede obtener tokens.

---

## Pregunta 5 — cursor_next_ms

`cursor_next_ms` en `etl_audit` almacena el `MAX(played_at)` en Unix milliseconds de la última ejecución exitosa. Sirve para implementar **carga incremental**: en la próxima ejecución el ETL pasa ese valor al parámetro `after` del endpoint de Spotify, trayendo solo las reproducciones nuevas desde ese momento.

Resuelve el problema de duplicación y eficiencia: sin el cursor, cada ejecución cargaría las mismas 50 reproducciones recientes sin importar si ya existen.

Si se escuchan 80 canciones en un día sin correr el ETL, el endpoint `recently-played` de Spotify solo devuelve las últimas 50 reproducciones. Las 30 anteriores se perderían permanentemente porque Spotify no guarda más de 50 en ese endpoint. Por eso el profe recomienda correr el ETL todos los días.