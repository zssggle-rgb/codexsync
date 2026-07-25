"""Command-line interface for codexsync."""

from __future__ import annotations

import sys
from typing import List, Optional

from . import __version__, config, switcher, sync
from .constants import APP_DISPLAY


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------
def cmd_status(_args: List[str]) -> int:
    provider, model = config.read_current()
    print(f"codexsync v{__version__}\n")
    print(f"Current provider:  {provider or '(unknown)'}")
    print(f"Current model:     {model or '(unknown)'}")
    print()

    # DB lock status
    locked = sync.check_locked()
    if locked:
        print(f"Database lock: {', '.join(locked)} — quit {APP_DISPLAY} to modify")
    else:
        print("Database lock:   none (safe to modify)")
    print()

    # SQLite: threads
    s_rows = sync.state_status()
    if s_rows is not None:
        print("threads table (state_5.sqlite):")
        for row in s_rows:
            print(f"  {row[0]}/{row[1]}: {row[2]}")
    print()

    # SQLite: catalog
    c_rows = sync.catalog_status()
    if c_rows is not None:
        print("local_thread_catalog (codex-dev.db):")
        for row in c_rows:
            print(f"  {row[0]}: {row[1]}")
    print()

    # Session files
    sessions = sync.scan_sessions()
    p_stats: dict = {}
    for _f, p, _m in sessions:
        p_stats[p] = p_stats.get(p, 0) + 1
    print(f"Session files ({len(sessions)} total):")
    for p, c in sorted(p_stats.items(), key=lambda x: -x[1]):
        print(f"  {p}: {c}")
    print()

    if locked:
        print("To sync sessions, first quit the app:")
        print(f"  osascript -e 'quit app \"{APP_DISPLAY.split(' / ')[0]}\"'")
    return 0


def cmd_switch(args: List[str]) -> int:
    if not args:
        print("Usage: codexsync switch <provider>")
        print("\nAvailable providers:")
        for name, cfg in config.available_providers().items():
            cur_p, _ = config.read_current()
            marker = " <- current" if cfg.get("model_provider") == cur_p else ""
            print(f"  {name:<16} model={cfg.get('model', '?')}, provider={cfg.get('model_provider', '?')}{marker}")
        return 1

    name = args[0].lower().strip()
    print(f"=== Switching to {name} ===\n")

    result = switcher.switch(name)
    if not result.get("ok"):
        print(f"Error: {result.get('error', 'unknown error')}")
        print("\nAvailable providers:")
        for n, cfg in config.available_providers().items():
            print(f"  {n}")
        return 1

    if result.get("already_active"):
        print(f"Already using {name}. Run 'codexsync sync' to re-sync sessions.")
        return 0

    print(f"Config updated    -> model={result['model']}, provider={result['model_provider']}")
    if result.get("config_backup"):
        print(f"Config backup     -> {result['config_backup']}")
    print(f"App restarted     -> {APP_DISPLAY}")

    s = result.get("sync", {})
    print(f"Sessions synced   -> {s.get('sessions_changed', 0)}/{s.get('sessions_total', 0)} files")
    print(f"Threads updated   -> {s.get('threads', 0)}")
    print(f"Catalog updated   -> {s.get('catalog', 0)}")
    print(f"\nDone. All historical sessions are now visible under {name}.")
    return 0


def cmd_sync(_args: List[str]) -> int:
    provider, model = config.read_current()
    if not provider:
        print("Error: cannot read model_provider from config.toml")
        return 1

    print(f"Target: {provider}/{model}\n")

    locked = sync.check_locked()
    if locked:
        print(f"Error: databases are locked ({', '.join(locked)}).")
        print(f"Quit {APP_DISPLAY} first:")
        print(f"  osascript -e 'quit app \"{APP_DISPLAY.split(' / ')[0]}\"'")
        return 1

    stats = sync.sync_all(provider, model or "")
    print(f"Threads updated    -> {stats['threads']}")
    print(f"Catalog updated    -> {stats['catalog']}")
    print(f"Sessions synced    -> {stats['sessions_changed']}/{stats['sessions_total']}")
    print(f"\nDone. Restart {APP_DISPLAY} to see all sessions.")
    return 0


def cmd_restore(_args: List[str]) -> int:
    locked = sync.check_locked()
    if locked:
        print(f"Error: databases are locked ({', '.join(locked)}).")
        print(f"Quit {APP_DISPLAY} first.")
        return 1

    print("Restoring to pre-sync state...\n")
    stats = sync.restore_all()
    print(f"Threads restored    -> {stats['threads']}")
    print(f"Catalog restored    -> {stats['catalog']}")
    print(f"Sessions restored   -> {stats['sessions']}")
    print(f"\nDone. Restart {APP_DISPLAY}.")
    return 0


def cmd_providers(_args: List[str]) -> int:
    cur_p, _ = config.read_current()
    print("Available providers:\n")
    for name, cfg in config.available_providers().items():
        active = " <- current" if cfg.get("model_provider") == cur_p else ""
        print(f"  {name:<16} model={cfg.get('model', '?')}, provider={cfg.get('model_provider', '?')}{active}")
    print("\nSwitch with: codexsync switch <name>")
    return 0


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
COMMANDS = {
    "status": cmd_status,
    "switch": cmd_switch,
    "sync": cmd_sync,
    "restore": cmd_restore,
    "providers": cmd_providers,
}


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])

    if not argv or argv[0] in ("-h", "--help", "help"):
        print(f"codexsync v{__version__}")
        print(f"Seamlessly switch Codex model providers without losing session history.\n")
        print("Usage: codexsync <command> [args]\n")
        print("Commands:")
        print("  status      Show current provider and session distribution")
        print("  switch <p>  Switch to provider <p> (openai, deepseek, or a profile name)")
        print("  sync        Sync sessions to current provider (no config change)")
        print("  restore     Undo the last sync")
        print("  providers   List available providers")
        print("\nOptions:")
        print("  -h, --help  Show this help")
        print("  -v, --version  Show version")
        return 0

    if argv[0] in ("-v", "--version"):
        print(__version__)
        return 0

    cmd = argv[0].lower().strip()
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS)}")
        return 1

    return COMMANDS[cmd](argv[1:])
