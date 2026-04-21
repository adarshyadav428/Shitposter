from __future__ import annotations

import json
from pathlib import Path

from newsbot.state.store import StateStore


def load_snapshot(path: str) -> StateStore | None:
    snapshot_path = Path(path)
    if not snapshot_path.exists():
        return None
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    try:
        return StateStore.from_dict(payload)
    except Exception:
        return None


def save_snapshot(path: str, store: StateStore) -> None:
    snapshot_path = Path(path)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = snapshot_path.with_suffix(snapshot_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(store.to_dict(), indent=2), encoding="utf-8")
    temp_path.replace(snapshot_path)
