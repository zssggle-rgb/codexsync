"""Synchronise the ``model_provider`` field across all Codex data stores.

Codex filters visible sessions by ``model_provider``.  That field is
duplicated across three locations:

1. ``~/.codex/state_5.sqlite`` — ``threads`` table (desktop task list).
2. ``~/.codex/sqlite/codex-dev.db`` — ``local_thread_catalog`` table.
3. ``~/.codex/sessions/**/*.jsonl`` — each file's first ``session_meta`` line.

Updating all three to the current provider restores full session visibility.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import CATALOG_DB, MANIFEST_DIR, SESSIONS_GLOB, STATE_DB


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------
def _ensure_manifest_dir() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def _manifest_path(name: str) -> Path:
    _ensure_manifest_dir()
    return MANIFEST_DIR / f"{name}.json"


def _save_manifest(name: str, data: dict) -> None:
    data["saved_at"] = datetime.now().isoformat()
    _manifest_path(name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_manifest(name: str) -> Optional[dict]:
    p = _manifest_path(name)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# SQLite lock check
# ---------------------------------------------------------------------------
def is_db_locked(db_path: Path) -> bool:
    """Return ``True`` if *db_path* is locked by another process."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=0.5)
        conn.execute("BEGIN EXCLUSIVE")
        conn.execute("COMMIT")
        conn.close()
        return False
    except sqlite3.OperationalError:
        return True


def _db_backup(db_path: Path) -> Path:
    bak = db_path.with_name(db_path.name + f".bak.{datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(db_path, bak)
    return bak


# ---------------------------------------------------------------------------
# state_5.sqlite — threads table
# ---------------------------------------------------------------------------
def state_status() -> Optional[List[Tuple[str, str, int]]]:
    if not STATE_DB.exists():
        return None
    conn = sqlite3.connect(str(STATE_DB))
    rows = conn.execute(
        "SELECT model_provider, model, COUNT(*) FROM threads "
        "GROUP BY model_provider, model ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()
    return rows


def state_sync(provider: str, model: str) -> Tuple[int, Optional[Path]]:
    if not STATE_DB.exists():
        return 0, None
    bak = _db_backup(STATE_DB)
    conn = sqlite3.connect(str(STATE_DB))
    records = [
        {"id": r[0], "old_provider": r[1], "old_model": r[2]}
        for r in conn.execute("SELECT id, model_provider, model FROM threads")
    ]
    updated = conn.execute(
        "UPDATE threads SET model_provider = ?, model = ?", (provider, model)
    ).rowcount
    conn.commit()
    conn.close()
    _save_manifest("state", {"backup": str(bak), "count": updated, "records": records})
    return updated, bak


def state_restore() -> int:
    m = _load_manifest("state")
    if not m:
        return 0
    conn = sqlite3.connect(str(STATE_DB))
    for rec in m["records"]:
        conn.execute(
            "UPDATE threads SET model_provider = ?, model = ? WHERE id = ?",
            (rec["old_provider"], rec["old_model"], rec["id"]),
        )
    conn.commit()
    conn.close()
    return len(m["records"])


# ---------------------------------------------------------------------------
# codex-dev.db — local_thread_catalog table
# ---------------------------------------------------------------------------
def catalog_status() -> Optional[List[Tuple[str, int]]]:
    if not CATALOG_DB.exists():
        return None
    conn = sqlite3.connect(str(CATALOG_DB))
    rows = conn.execute(
        "SELECT model_provider, COUNT(*) FROM local_thread_catalog "
        "GROUP BY model_provider ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()
    return rows


def catalog_sync(provider: str, model: str) -> Tuple[int, Optional[Path]]:
    if not CATALOG_DB.exists():
        return 0, None
    bak = _db_backup(CATALOG_DB)
    conn = sqlite3.connect(str(CATALOG_DB))
    records = [
        {"thread_id": r[0], "old_provider": r[1]}
        for r in conn.execute("SELECT thread_id, model_provider FROM local_thread_catalog")
    ]
    updated = conn.execute(
        "UPDATE local_thread_catalog SET model_provider = ?", (provider,)
    ).rowcount
    conn.commit()
    conn.close()
    _save_manifest("catalog", {"backup": str(bak), "count": updated, "records": records})
    return updated, bak


def catalog_restore() -> int:
    m = _load_manifest("catalog")
    if not m:
        return 0
    conn = sqlite3.connect(str(CATALOG_DB))
    for rec in m["records"]:
        conn.execute(
            "UPDATE local_thread_catalog SET model_provider = ? WHERE thread_id = ?",
            (rec["old_provider"], rec["thread_id"]),
        )
    conn.commit()
    conn.close()
    return len(m["records"])


# ---------------------------------------------------------------------------
# Session JSONL files
# ---------------------------------------------------------------------------
def scan_sessions() -> List[Tuple[str, str, str]]:
    """Return ``[(filepath, provider, model), ...]`` for every session file."""
    results: List[Tuple[str, str, str]] = []
    for f in sorted(glob.glob(SESSIONS_GLOB, recursive=True)):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                first = fh.readline().strip()
                if not first:
                    continue
                d = json.loads(first)
                if d.get("type") != "session_meta":
                    continue
                payload = d.get("payload", {})
                results.append(
                    (f, payload.get("model_provider", "unknown"), payload.get("model", "unknown"))
                )
        except (json.JSONDecodeError, OSError):
            continue
    return results


def _patch_session(filepath: str, provider: str, model: Optional[str]) -> Optional[Tuple[str, str]]:
    with open(filepath, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    if not lines:
        return None
    first = json.loads(lines[0].strip())
    if first.get("type") != "session_meta":
        return None
    payload = first.get("payload", {})
    old = (payload.get("model_provider", "unknown"), payload.get("model", "unknown"))
    payload["model_provider"] = provider
    if model:
        payload["model"] = model
    first["payload"] = payload
    lines[0] = json.dumps(first, ensure_ascii=False) + "\n"
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    return old


def sessions_sync(provider: str, model: str) -> Tuple[int, int]:
    sessions = scan_sessions()
    records: List[dict] = []
    changed = 0
    for f, _old_p, _old_m in sessions:
        result = _patch_session(f, provider, model)
        if result:
            records.append({"file": f, "old_provider": result[0], "old_model": result[1]})
            changed += 1
    _save_manifest("sessions", {"count": changed, "records": records})
    return changed, len(sessions)


def sessions_restore() -> int:
    m = _load_manifest("sessions")
    if not m:
        return 0
    restored = 0
    for rec in m["records"]:
        f = rec["file"]
        if not os.path.exists(f):
            continue
        with open(f, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        if not lines:
            continue
        first = json.loads(lines[0].strip())
        if first.get("type") != "session_meta":
            continue
        payload = first.get("payload", {})
        payload["model_provider"] = rec["old_provider"]
        payload["model"] = rec["old_model"]
        first["payload"] = payload
        lines[0] = json.dumps(first, ensure_ascii=False) + "\n"
        with open(f, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
        restored += 1
    return restored


# ---------------------------------------------------------------------------
# High-level orchestration
# ---------------------------------------------------------------------------
def check_locked() -> List[str]:
    """Return names of databases that are currently locked."""
    locked: List[str] = []
    for label, db in [("state_5.sqlite", STATE_DB), ("codex-dev.db", CATALOG_DB)]:
        if db.exists() and is_db_locked(db):
            locked.append(label)
    return locked


def sync_all(provider: str, model: str) -> Dict[str, int]:
    """Sync all three data stores. Call *after* the app has been quit."""
    s_count, _ = state_sync(provider, model)
    c_count, _ = catalog_sync(provider, model)
    changed, total = sessions_sync(provider, model)
    return {
        "threads": s_count,
        "catalog": c_count,
        "sessions_changed": changed,
        "sessions_total": total,
    }


def restore_all() -> Dict[str, int]:
    """Restore all three data stores to pre-sync values."""
    return {
        "threads": state_restore(),
        "catalog": catalog_restore(),
        "sessions": sessions_restore(),
    }
