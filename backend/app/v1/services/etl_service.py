import time
from datetime import datetime, timezone
import psycopg2
from app.core.config import settings
from app.core.spotify_client import spotify_get
from app.v1.services.auth_service import get_valid_spotify_token, upsert_user
from app.v1.services.artists_service import extract_top_artists, load_artists, transform_top_artists
from app.v1.services.history_service import extract_recently_played, load_history, transform_recently_played
from app.v1.services.tracks_service import extract_top_tracks, load_tracks, transform_top_tracks

def _get_conn():
    return psycopg2.connect(settings.DATABASE_URL)

def _get_user_id(conn, spotify_user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM dwh.dim_users WHERE spotify_id = %s", (spotify_user_id,))
        row = cur.fetchone()
    return row[0] if row else None

def _get_last_cursor(conn, spotify_user_id):
    with conn.cursor() as cur:
        cur.execute("""SELECT cursor_next_ms FROM dwh.etl_audit
            WHERE spotify_user_id = %s AND status = 'success'
            ORDER BY started_at DESC LIMIT 1""", (spotify_user_id,))
        row = cur.fetchone()
    return row[0] if row else None

def _get_max_played_at_ms(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(played_at) FROM dwh.fact_listening_history WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
    if row and row[0]:
        ts = row[0]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return int(ts.timestamp() * 1000)
    return None

def _insert_audit_start(conn, spotify_user_id):
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO dwh.etl_audit (spotify_user_id, started_at, status)
            VALUES (%s, %s, 'running') RETURNING audit_id""",
            (spotify_user_id, datetime.now(timezone.utc)))
        audit_id = cur.fetchone()[0]
    conn.commit()
    return audit_id

def _update_audit_success(conn, audit_id, duration_ms, cursor_after_ms, cursor_next_ms, **metrics):
    with conn.cursor() as cur:
        cur.execute("""UPDATE dwh.etl_audit SET
            finished_at=%s, duration_ms=%s, status='success',
            users_new=%s, artists_new=%s, artists_skipped=%s,
            tracks_new=%s, tracks_skipped=%s, history_new=%s, history_skipped=%s,
            cursor_after_ms=%s, cursor_next_ms=%s WHERE audit_id=%s""",
            (datetime.now(timezone.utc), duration_ms,
             metrics.get("users_new",0), metrics.get("artists_new",0), metrics.get("artists_skipped",0),
             metrics.get("tracks_new",0), metrics.get("tracks_skipped",0),
             metrics.get("history_new",0), metrics.get("history_skipped",0),
             cursor_after_ms, cursor_next_ms, audit_id))
    conn.commit()

def _update_audit_error(conn, audit_id, duration_ms, error_message):
    with conn.cursor() as cur:
        cur.execute("""UPDATE dwh.etl_audit SET finished_at=%s, duration_ms=%s,
            status='error', error_message=%s WHERE audit_id=%s""",
            (datetime.now(timezone.utc), duration_ms, error_message, audit_id))
    conn.commit()

def run_etl(spotify_user_id):
    conn = _get_conn()
    audit_id = _insert_audit_start(conn, spotify_user_id)
    t0 = time.time()
    try:
        token = get_valid_spotify_token(spotify_user_id)
        cursor_after_ms = _get_last_cursor(conn, spotify_user_id)
        metrics = {"users_new":0,"artists_new":0,"artists_skipped":0,
                   "tracks_new":0,"tracks_skipped":0,"history_new":0,"history_skipped":0}

        user_id_before = _get_user_id(conn, spotify_user_id)
        spotify_profile = spotify_get("/me", token)
        upsert_user(spotify_profile, {"access_token": token, "expires_in": 3600})
        metrics["users_new"] = 0 if user_id_before else 1
        user_id = _get_user_id(conn, spotify_user_id)

        raw_artists = extract_top_artists(token)
        artists = transform_top_artists(raw_artists)
        a_ins, a_skip = load_artists(artists)
        metrics["artists_new"] = a_ins
        metrics["artists_skipped"] = a_skip

        raw_tracks = extract_top_tracks(token)
        tracks = transform_top_tracks(raw_tracks)
        t_ins, t_skip = load_tracks(tracks)
        metrics["tracks_new"] = t_ins
        metrics["tracks_skipped"] = t_skip

        raw_history = extract_recently_played(token, after_ms=cursor_after_ms)
        history_items = transform_recently_played(raw_history)
        h_ins, h_skip = load_history(history_items, user_id)
        metrics["history_new"] = h_ins
        metrics["history_skipped"] = h_skip
        
        from app.v1.services.history_service import extract_artists_from_history
        history_artists = extract_artists_from_history(raw_history)
        if history_artists:
            h_a_ins, h_a_skip = load_artists(history_artists)
            metrics["artists_new"] += h_a_ins
            metrics["artists_skipped"] += h_a_skip
        
        from app.v1.services.history_service import extract_tracks_from_history
        history_tracks = extract_tracks_from_history(raw_history)
        if history_tracks:
            h_t_ins, h_t_skip = load_tracks(history_tracks)
            metrics["tracks_new"] += h_t_ins
            metrics["tracks_skipped"] += h_t_skip

        cursor_next_ms = _get_max_played_at_ms(conn, user_id)
        duration_ms = int((time.time() - t0) * 1000)
        _update_audit_success(conn, audit_id, duration_ms=duration_ms,
            cursor_after_ms=cursor_after_ms, cursor_next_ms=cursor_next_ms, **metrics)
        return {"status": "success", "duration_ms": duration_ms, **metrics, "cursor_next_ms": cursor_next_ms}

    except Exception as exc:
        duration_ms = int((time.time() - t0) * 1000)
        _update_audit_error(conn, audit_id, duration_ms, str(exc))
        raise
    finally:
        conn.close()

def get_etl_status(spotify_user_id, limit=20):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT audit_id, started_at, finished_at, duration_ms, status,
                error_message, users_new, artists_new, artists_skipped,
                tracks_new, tracks_skipped, history_new, history_skipped,
                cursor_after_ms, cursor_next_ms
                FROM dwh.etl_audit WHERE spotify_user_id = %s
                ORDER BY started_at DESC LIMIT %s""", (spotify_user_id, limit))
            rows = cur.fetchall()
    cols = ["audit_id","started_at","finished_at","duration_ms","status","error_message",
            "users_new","artists_new","artists_skipped","tracks_new","tracks_skipped",
            "history_new","history_skipped","cursor_after_ms","cursor_next_ms"]
    return [dict(zip(cols, row)) for row in rows]