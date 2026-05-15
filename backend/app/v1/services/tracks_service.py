import psycopg2
from app.core.config import settings
from app.core.spotify_client import spotify_get

def _get_conn():
    return psycopg2.connect(settings.DATABASE_URL)

def extract_top_tracks(token):
    data = spotify_get("/me/top/tracks", token, params={"limit": 50, "time_range": "medium_term"})
    return data.get("items", [])

def transform_top_tracks(raw_tracks):
    result = []
    for item in raw_tracks:
        artists = item.get("artists", [])
        result.append({
            "spotify_id": item["id"],
            "name": item["name"],
            "artist_spotify_id": artists[0]["id"] if artists else None,
            "album_name": item.get("album", {}).get("name"),
            "duration_ms": item.get("duration_ms"),
            "popularity": item.get("popularity"),
            "explicit": item.get("explicit"),
        })
    return result

def load_tracks(tracks):
    inserted = 0
    skipped = 0
    with _get_conn() as conn:
        with conn.cursor() as cur:
            for t in tracks:
                artist_id = None
                if t["artist_spotify_id"]:
                    cur.execute("SELECT artist_id FROM dwh.dim_artists WHERE spotify_id = %s", (t["artist_spotify_id"],))
                    row = cur.fetchone()
                    if row:
                        artist_id = row[0]
                cur.execute("""INSERT INTO dwh.dim_tracks
                    (spotify_id, name, artist_id, album_name, duration_ms, popularity, explicit, loaded_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
                    ON CONFLICT (spotify_id) DO NOTHING""",
                    (t["spotify_id"], t["name"], artist_id, t["album_name"],
                     t["duration_ms"], t["popularity"], t["explicit"]))
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1
        conn.commit()
    return inserted, skipped

def get_top_tracks_from_db(spotify_id):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT t.track_id, t.spotify_id, t.name, t.artist_id,
                       t.album_name, t.duration_ms, t.popularity, t.explicit,
                       t.loaded_at, COUNT(f.id) AS play_count
                FROM dwh.dim_tracks t
                JOIN dwh.fact_listening_history f ON f.track_id = t.track_id
                JOIN dwh.dim_users u ON u.user_id = f.user_id
                WHERE u.spotify_id = %s
                GROUP BY t.track_id
                ORDER BY play_count DESC
                LIMIT 50""", (spotify_id,))
            rows = cur.fetchall()
    cols = ["track_id","spotify_id","name","artist_id","album_name","duration_ms","popularity","explicit","loaded_at","play_count"]
    return [dict(zip(cols, row)) for row in rows]