# Consultas Analíticas — Mi Spotify Wrapped

**Autor:** Carlos Camargo
**Fecha:** 2026-05-14

---

## Pregunta 1 — ¿En qué hora del día escuchas más música?

```sql
SELECT hour_of_day, COUNT(*) AS reproducciones
FROM dwh.fact_listening_history
GROUP BY hour_of_day
ORDER BY reproducciones DESC;
```

**Interpretación:** Esta query agrupa todas las reproducciones por hora del día (0-23) y las ordena de mayor a menor. La hora con más reproducciones revela el pico de escucha personal.

---

## Pregunta 2 — ¿Cuál es tu artista más escuchado?

```sql
SELECT a.name, COUNT(*) AS veces
FROM dwh.fact_listening_history f
JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
GROUP BY a.name
ORDER BY veces DESC
LIMIT 5;
```

**Interpretación:** El JOIN entre la tabla de hechos y `dim_artists` permite resolver el nombre del artista. Los primeros 5 resultados forman el top 5 artistas basado en datos reales de escucha.

---

## Pregunta 3 — ¿Qué tan popular es tu música?

```sql
SELECT AVG(popularity) AS popularidad_promedio,
       MIN(popularity) AS mas_underground,
       MAX(popularity) AS mas_mainstream
FROM dwh.dim_tracks;
```

**Interpretación:** La popularidad en Spotify va de 0 a 100. Un promedio alto indica gusto mainstream; un valor bajo sugiere preferencia por música independiente.

---

## Pregunta 4 — ¿Cuáles géneros dominan tu biblioteca?

```sql
SELECT UNNEST(genres) AS genero, COUNT(*) AS artistas
FROM dwh.dim_artists
GROUP BY genero
ORDER BY artistas DESC
LIMIT 10;
```

**Interpretación:** `UNNEST` explota el array `TEXT[]` de géneros en filas individuales. El resultado muestra el ADN musical personal.

---

## Pregunta 5 — Ranking de canciones por día de semana

```sql
SELECT day_of_week, t.name, COUNT(*) AS plays,
       RANK() OVER (PARTITION BY day_of_week ORDER BY COUNT(*) DESC) AS ranking
FROM dwh.fact_listening_history f
JOIN dwh.dim_tracks t ON t.track_id = f.track_id
GROUP BY day_of_week, t.name;
```

**Interpretación:** `RANK() OVER (PARTITION BY day_of_week)` asigna un ranking independiente por cada día de la semana, revelando si los hábitos musicales cambian según el día.

---

## Screenshots

[Insertar capturas de los resultados de cada query en Neon]