from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nexusrouter:nexusrouter@localhost:5433/nexusrouter"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def init_db():
    """Creates all audit tables if they don't exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS event_log (
                id               SERIAL PRIMARY KEY,
                event_id         TEXT UNIQUE NOT NULL,
                source           TEXT NOT NULL,
                sender           TEXT,
                subject          TEXT,
                intent           TEXT,
                secondary_intents TEXT,
                urgency          TEXT,
                target_agent     TEXT,
                confidence       FLOAT,
                entities         TEXT,
                reasoning        TEXT,
                applied_rules    TEXT,
                require_hitl     BOOLEAN DEFAULT FALSE,
                route_to         TEXT,
                raw_text_preview TEXT,
                received_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS action_log (
                id           SERIAL PRIMARY KEY,
                event_id     TEXT REFERENCES event_log(event_id),
                agent        TEXT NOT NULL,
                action_type  TEXT NOT NULL,
                action_input TEXT,
                action_output TEXT,
                status       TEXT NOT NULL,
                error        TEXT,
                executed_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        conn.commit()
    print("[audit] Database tables initialized.")
