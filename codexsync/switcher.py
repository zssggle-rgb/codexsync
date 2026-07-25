"""High-level provider switching: edit config → quit app → sync → reopen."""

from __future__ import annotations

import subprocess
import time
from typing import Dict, Optional

from . import config
from . import sync
from .constants import APP_NAME


def quit_app() -> bool:
    """Gracefully quit the Codex desktop app, force-kill if needed."""
    subprocess.run(["osascript", "-e", f'quit app "{APP_NAME}"'], capture_output=True)
    for _ in range(10):
        time.sleep(1)
        r = subprocess.run(["pgrep", "-fil", APP_NAME], capture_output=True, text=True)
        if not r.stdout.strip():
            return True
    # still running — force kill
    subprocess.run(["pkill", "-f", APP_NAME], capture_output=True)
    time.sleep(2)
    return True


def open_app() -> None:
    subprocess.run(["open", "-a", APP_NAME], capture_output=True)


def resolve_target(name: str) -> Optional[Dict[str, str]]:
    """Resolve a provider name to ``{model, model_provider}``.

    Checks user-defined ``[profiles.*]`` first, then built-in defaults.
    """
    providers = config.available_providers()
    if name in providers:
        p = providers[name]
        if "model" in p and "model_provider" in p:
            return p
    return None


def switch(name: str) -> Dict:
    """Switch to *name* provider. Returns a result dict with details."""
    target = resolve_target(name)
    if target is None:
        return {"ok": False, "error": f"Unknown provider: {name}"}

    cur_provider, cur_model = config.read_current()
    if cur_provider == target["model_provider"] and cur_model == target["model"]:
        return {"ok": True, "already_active": True, "provider": name}

    # 1. Patch config.toml
    bak = config.patch_top_level(target["model"], target["model_provider"])

    # 2. Quit app
    quit_app()

    # 3. Sync sessions
    stats = sync.sync_all(target["model_provider"], target["model"])

    # 4. Reopen app
    open_app()

    return {
        "ok": True,
        "provider": name,
        "model": target["model"],
        "model_provider": target["model_provider"],
        "config_backup": str(bak) if bak else None,
        "sync": stats,
    }
