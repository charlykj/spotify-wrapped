import psycopg2
from app.core.config import settings

def _get_conn():
    return psycopg2.connect(settings.DATABASE_URL)

def get_profile(spotify_id):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT user_id, spotify_id, display_name, email,
                country, followers, product, loaded_at
                FROM dwh.dim_users WHERE spotify_id = %s""", (spotify_id,))
            row = cur.fetchone()
    if not row:
        return None
    cols = ["user_id","spotify_id","display_name","email","country","followers","product","loaded_at"]
    return dict(zip(cols, row))