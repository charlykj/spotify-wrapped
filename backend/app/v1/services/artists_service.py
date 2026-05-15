import psycopg2
from app.core.config import settings
from app.core.spotify_client import spotify_get

def _get_conn():
    return psycopg2.connect(settings.DATABASE_URL)

def extract_top_artists(token):
    data = spotify_get("/me/top/artists", token, params={"limit": 50, "time_range": "medium_term"})
    return data.get("items", [])

def transform_top_artists(raw_artists):
    result = []
    for item in raw_artists:
        result.append({
            "spotify_id": item["id"],
            "name": item["name"],
            "popularity": item.get("popularity"),
            "followers_count": item.get("followers", {}).get("total"),
            "genres": item.get("genres", []),
        })
    return result

def load_artists(artists):
    inserted = 0
    skipped = 0
    with _get_conn() as conn:
        with conn.cursor() as cur:
            for a in artists:
                cur.execute("""INSERT INTO dwh.dim_artists
                    (spotify_id, name, popularity, followers_count, genres, loaded_at)
                    VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
                    ON CONFLICT (spotify_id) DO NOTHING""",
                    (a["spotify_id"], a["name"], a["popularity"], a["followers_count"], a["genres"]))
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1
        conn.commit()
    return inserted, skipped

def get_top_artists_from_db(spotify_id):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT a.artist_id, a.spotify_id, a.name, a.popularity,
                       a.followers_count, a.genres, a.loaded_at, COUNT(f.id) AS play_count
                FROM dwh.dim_artists a
                JOIN dwh.fact_listening_history f ON f.artist_id = a.artist_id
                JOIN dwh.dim_users u ON u.user_id = f.user_id
                WHERE u.spotify_id = %s
                GROUP BY a.artist_id
                ORDER BY play_count DESC
                LIMIT 50""", (spotify_id,))
            rows = cur.fetchall()
    cols = ["artist_id","spotify_id","name","popularity","followers_count","genres","loaded_at","play_count"]
    return [dict(zip(cols, row)) for row in rows]