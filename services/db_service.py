
from pathlib import Path
import sqlite3, json, datetime

DB_PATH = Path(__file__).resolve().parent.parent / "akensya_events.db"

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            entity TEXT,
            payload TEXT,
            created_at TEXT
        )""")

def save_event(event_type, entity, payload):
    init_db()
    with _conn() as c:
        c.execute(
            "INSERT INTO events(event_type,entity,payload,created_at) VALUES(?,?,?,?)",
            (event_type, entity, json.dumps(payload), datetime.datetime.utcnow().isoformat())
        )
