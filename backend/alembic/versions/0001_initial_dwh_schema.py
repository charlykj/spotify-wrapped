from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS dwh")
    op.execute("""CREATE TABLE IF NOT EXISTS public.pkce_sessions (state VARCHAR(128) PRIMARY KEY, verifier TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE IF NOT EXISTS dwh.dim_users (user_id SERIAL PRIMARY KEY, spotify_id VARCHAR(100) UNIQUE NOT NULL, display_name VARCHAR(255), email VARCHAR(255), country VARCHAR(10), followers INT, product VARCHAR(20), spotify_access_token TEXT, spotify_refresh_token TEXT, token_expires_at TIMESTAMP, loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE IF NOT EXISTS dwh.dim_artists (artist_id SERIAL PRIMARY KEY, spotify_id VARCHAR(100) UNIQUE NOT NULL, name VARCHAR(255) NOT NULL, popularity INT, followers_count INT, genres TEXT[], loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE IF NOT EXISTS dwh.dim_tracks (track_id SERIAL PRIMARY KEY, spotify_id VARCHAR(100) UNIQUE NOT NULL, name VARCHAR(255) NOT NULL, artist_id INT REFERENCES dwh.dim_artists(artist_id), album_name VARCHAR(255), duration_ms INT, popularity INT, explicit BOOLEAN, loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    op.execute("""CREATE TABLE IF NOT EXISTS dwh.fact_listening_history (id SERIAL PRIMARY KEY, user_id INT NOT NULL REFERENCES dwh.dim_users(user_id), track_id INT NOT NULL REFERENCES dwh.dim_tracks(track_id), artist_id INT NOT NULL REFERENCES dwh.dim_artists(artist_id), played_at TIMESTAMP NOT NULL, hour_of_day INT, day_of_week VARCHAR(10), context_type VARCHAR(50), UNIQUE (user_id, played_at))""")
    op.execute("""CREATE TABLE IF NOT EXISTS dwh.etl_audit (audit_id SERIAL PRIMARY KEY, spotify_user_id VARCHAR(100) NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, duration_ms INT, status VARCHAR(20) NOT NULL, error_message TEXT, users_new INT DEFAULT 0, artists_new INT DEFAULT 0, artists_skipped INT DEFAULT 0, tracks_new INT DEFAULT 0, tracks_skipped INT DEFAULT 0, history_new INT DEFAULT 0, history_skipped INT DEFAULT 0, cursor_after_ms BIGINT, cursor_next_ms BIGINT)""")

def downgrade():
    op.execute("DROP TABLE IF EXISTS dwh.fact_listening_history")
    op.execute("DROP TABLE IF EXISTS dwh.etl_audit")
    op.execute("DROP TABLE IF EXISTS dwh.dim_tracks")
    op.execute("DROP TABLE IF EXISTS dwh.dim_artists")
    op.execute("DROP TABLE IF EXISTS dwh.dim_users")
    op.execute("DROP TABLE IF EXISTS public.pkce_sessions")
    op.execute("DROP SCHEMA IF EXISTS dwh")
