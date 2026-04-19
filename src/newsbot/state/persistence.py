from __future__ import annotations

from newsbot.config import settings
from newsbot.state.snapshot import load_snapshot, save_snapshot
from newsbot.state.sqlite_snapshot import load_sqlite_snapshot, save_sqlite_snapshot
from newsbot.state.store import StateStore


def load_state(path_override: str | None = None) -> StateStore | None:
    backend = (settings.state_backend or "json").lower()
    if backend == "sqlite":
        sqlite_path = path_override or settings.state_sqlite_path
        loaded = load_sqlite_snapshot(sqlite_path)
        if loaded is not None:
            return loaded

        # Backward-compatible bootstrap: if SQLite is empty but JSON state exists,
        # import it once into SQLite so operators can switch backends safely.
        if path_override is None:
            fallback = load_snapshot(settings.state_snapshot_path)
            if fallback is not None:
                save_sqlite_snapshot(settings.state_sqlite_path, fallback)
                return fallback
        return None
    return load_snapshot(path_override or settings.state_snapshot_path)


def save_state(store: StateStore, path_override: str | None = None) -> None:
    backend = (settings.state_backend or "json").lower()
    if backend == "sqlite":
        save_sqlite_snapshot(path_override or settings.state_sqlite_path, store)
        return
    save_snapshot(path_override or settings.state_snapshot_path, store)


def default_state_path() -> str:
    backend = (settings.state_backend or "json").lower()
    if backend == "sqlite":
        return settings.state_sqlite_path
    return settings.state_snapshot_path
