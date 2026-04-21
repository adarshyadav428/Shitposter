from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from newsbot.state.store import StateStore


def load_sqlite_snapshot(path: str) -> StateStore | None:
    db_path = Path(path)
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        try:
            _ensure_schema(conn)
            row = conn.execute("SELECT payload FROM state_snapshot WHERE id = 1").fetchone()
            if row is None:
                return None
            payload = json.loads(row[0])
            return StateStore.from_dict(payload)
        finally:
            conn.close()
    except Exception:
        return None


def save_sqlite_snapshot(path: str, store: StateStore) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_schema(conn)
        payload = json.dumps(store.to_dict())
        conn.execute(
            "INSERT INTO state_snapshot (id, payload) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (payload,),
        )
        conn.commit()
    finally:
        conn.close()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS state_snapshot ("
        "id INTEGER PRIMARY KEY CHECK (id = 1),"
        "payload TEXT NOT NULL"
        ")"
    )
