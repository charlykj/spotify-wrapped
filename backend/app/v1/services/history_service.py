from datetime import datetime, timezone
import psycopg2
from app.core.config import settings
from app.core.spotify_client import spotify_get

def _get_conn():
    return psycopg2.connect(settings.DATABASE_URL)

def played_at_to_unix_ms(played_at_iso):
    dt = datetime.fromisoformat(played_at_iso.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)

def extract_recently_played(token, after_ms=None):
    params = {"limit": 50}
    if after_ms is not None:
        params["after"] = after_ms
    data = spotify_get("/me/player/recently-played", token, params=params)
    return data.get("items", [])

def transform_recently_played(raw_items):
    result = []
    for item in raw_items:
        played_at_iso = item["played_at"]
        dt = datetime.fromisoformat(played_at_iso.replace("Z", "+00:00"))
        track = item.get("track", {})
        artists = track.get("artists", [])
        result.append({
            "track_spotify_id": track.get("id"),
            "artist_spotify_id": artists[0]["id"] if artists else None,
            "played_at": dt,
            "hour_of_day": dt.hour,
            "day_of_week": dt.strftime("%A"),
            "context_type": (item.get("context") or {}).get("type") or "unknown",
        })
    return result

def load_history(items, user_id):
    inserted = 0
    skipped = 0
    with _get_conn() as conn:
        with conn.cursor() as cur:
            for item in items:
                track_id = None
                if item["track_spotify_id"]:
                    cur.execute("SELECT track_id FROM dwh.dim_tracks WHERE spotify_id = %s", (item["track_spotify_id"],))
                    row = cur.fetchone()
                    if row:
                        track_id = row[0]
                artist_id = None
                if item["artist_spotify_id"]:
                    cur.execute("SELECT artist_id FROM dwh.dim_artists WHERE spotify_id = %s", (item["artist_spotify_id"],))
                    row = cur.fetchone()
                    if row:
                        artist_id = row[0]
                if not track_id or not artist_id:
                    skipped += 1
                    continue
                cur.execute("""INSERT INTO dwh.fact_listening_history
                    (user_id, track_id, artist_id, played_at, hour_of_day, day_of_week, context_type)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (user_id, played_at) DO NOTHING""",
                    (user_id, track_id, artist_id, item["played_at"],
                     item["hour_of_day"], item["day_of_week"], item["context_type"]))
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1
        conn.commit()
    return inserted, skipped

def get_recently_played_from_db(spotify_id, limit=50):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT f.id, f.user_id, f.track_id, f.artist_id,
                       f.played_at, f.hour_of_day, f.day_of_week, f.context_type,
                       t.name AS track_name, a.name AS artist_name
                FROM dwh.fact_listening_history f
                JOIN dwh.dim_users u ON u.user_id = f.user_id
                JOIN dwh.dim_tracks t ON t.track_id = f.track_id
                JOIN dwh.dim_artists a ON a.artist_id = f.artist_id
                WHERE u.spotify_id = %s
                ORDER BY f.played_at DESC
                LIMIT %s""", (spotify_id, limit))
            rows = cur.fetchall()
    cols = ["id","user_id","track_id","artist_id","played_at","hour_of_day","day_of_week","context_type","track_name","artist_name"]
    return [dict(zip(cols, row)) for row in rows]
def extract_artists_from_history(raw_items):
    artists = []
    seen = set()
    for item in raw_items:
        track = item.get("track", {})
        for artist in track.get("artists", []):
            spotify_id = artist.get("id")
            if spotify_id and spotify_id not in seen:
                seen.add(spotify_id)
                artists.append({
                    "spotify_id": spotify_id,
                    "name": artist.get("name"),
                    "popularity": None,
                    "followers_count": None,
                    "genres": []
                })
    return artists
def extract_tracks_from_history(raw_items):
    tracks = []
    seen = set()
    for item in raw_items:
        track = item.get("track", {})
        spotify_id = track.get("id")
        if spotify_id and spotify_id not in seen:
            seen.add(spotify_id)
            artists = track.get("artists", [])
            tracks.append({
                "spotify_id": spotify_id,
                "name": track.get("name"),
                "artist_spotify_id": artists[0]["id"] if artists else None,
                "album_name": track.get("album", {}).get("name"),
                "duration_ms": track.get("duration_ms"),
                "popularity": track.get("popularity"),
                "explicit": track.get("explicit")
            })
    return tracks