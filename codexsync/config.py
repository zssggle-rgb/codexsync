"""Read and patch Codex ``config.toml`` with surgical precision.

Only top-level keys (before the first ``[section]`` header) are modified so
that ``[profiles.*]`` blocks remain untouched.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from .constants import BUILTIN_PROVIDERS, CONFIG_TOML


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def read_current() -> Tuple[Optional[str], Optional[str]]:
    """Return ``(model_provider, model)`` from the top-level of config.toml.

    Only keys appearing *before* the first ``[section]`` header are read, so
    values inside ``[profiles.*]`` are never confused with the active config.
    """
    if not CONFIG_TOML.exists():
        return None, None

    model: Optional[str] = None
    provider: Optional[str] = None

    for line in CONFIG_TOML.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            break  # entered a section — top-level keys are above this
        m = re.match(r'^model\s*=\s*"([^"]+)"', stripped)
        if m:
            model = m.group(1)
        m = re.match(r'^model_provider\s*=\s*"([^"]+)"', stripped)
        if m:
            provider = m.group(1)

    return provider, model


def read_profiles() -> Dict[str, Dict[str, str]]:
    """Parse ``[profiles.<name>]`` sections into ``{name: {model, model_provider}}``."""
    if not CONFIG_TOML.exists():
        return {}

    profiles: Dict[str, Dict[str, str]] = {}
    current_name: Optional[str] = None
    current_data: Dict[str, str] = {}

    for line in CONFIG_TOML.read_text().splitlines():
        stripped = line.strip()
        m = re.match(r"^\[profiles\.(\w+)\]", stripped)
        if m:
            # save previous profile
            if current_name:
                profiles[current_name] = current_data
            current_name = m.group(1)
            current_data = {}
            continue
        if not stripped.startswith("[") and current_name:
            mm = re.match(r'^model\s*=\s*"([^"]+)"', stripped)
            if mm:
                current_data["model"] = mm.group(1)
            mm = re.match(r'^model_provider\s*=\s*"([^"]+)"', stripped)
            if mm:
                current_data["model_provider"] = mm.group(1)
        elif stripped.startswith("[") and current_name:
            # leaving the profile section
            profiles[current_name] = current_data
            current_name = None
            current_data = {}

    if current_name:
        profiles[current_name] = current_data

    return profiles


def available_providers() -> Dict[str, Dict[str, str]]:
    """Merge built-in defaults with user-defined profiles.

    User profiles take precedence over built-ins of the same name.
    """
    merged = dict(BUILTIN_PROVIDERS)
    merged.update(read_profiles())
    return merged


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
def patch_top_level(model: str, model_provider: str, backup: bool = True) -> Optional[Path]:
    """Replace top-level ``model`` / ``model_provider`` values in config.toml.

    Returns the backup path if a backup was made, otherwise ``None``.
    Raises ``FileNotFoundError`` if config.toml does not exist.
    """
    if not CONFIG_TOML.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_TOML}")

    text = CONFIG_TOML.read_text()
    lines = text.splitlines(keepends=True)

    bak_path: Optional[Path] = None
    if backup:
        bak_path = CONFIG_TOML.with_suffix(f".toml.bak.{datetime.now():%Y%m%d%H%M%S}")
        shutil.copy2(CONFIG_TOML, bak_path)

    model_done = False
    provider_done = False

    for i, line in enumerate(lines):
        if line.strip().startswith("["):
            break  # only touch top-level keys
        if not model_done:
            new = re.sub(r'(^model\s*=\s*)"[^"]*"', f'\\1"{model}"', line)
            if new != line:
                lines[i] = new
                model_done = True
        if not provider_done:
            new = re.sub(r'(^model_provider\s*=\s*)"[^"]*"', f'\\1"{model_provider}"', line)
            if new != line:
                lines[i] = new
                provider_done = True

    if not (model_done and provider_done):
        raise RuntimeError(
            "Could not locate top-level model/model_provider keys in config.toml"
        )

    CONFIG_TOML.write_text("".join(lines))
    return bak_path
