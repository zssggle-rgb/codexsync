"""Path constants and built-in provider defaults for codexsync."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CODEX_DIR = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
CONFIG_TOML = CODEX_DIR / "config.toml"
AUTH_JSON = CODEX_DIR / "auth.json"

# SQLite databases that store session metadata
STATE_DB = CODEX_DIR / "state_5.sqlite"
CATALOG_DB = CODEX_DIR / "sqlite" / "codex-dev.db"

# Session rollout files (JSONL)
SESSIONS_GLOB = str(CODEX_DIR / "sessions" / "**" / "*.jsonl")

# Manifest directory for backup/restore
MANIFEST_DIR = CODEX_DIR / "sync_manifests"

# ---------------------------------------------------------------------------
# Built-in provider defaults
# ---------------------------------------------------------------------------
# These are used as fallback when no matching [profiles.*] section exists in
# config.toml. Users can override by creating a profile of the same name.
BUILTIN_PROVIDERS: Dict[str, Dict[str, str]] = {
    "openai": {
        "model": "gpt-5.6-sol",
        "model_provider": "openai",
    },
    "deepseek": {
        "model": "deepseek-v4-pro",
        "model_provider": "deepseek",
    },
}

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
APP_NAME = "ChatGPT"  # The macOS bundle that hosts Codex desktop
APP_DISPLAY = "ChatGPT / Codex"
