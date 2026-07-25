# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-25

### Added
- **One-command provider switching** — `codexsync switch <provider>` automatically edits `config.toml`, quits the Codex desktop app, syncs all session metadata, and relaunches.
- **Session visibility fix** — synchronises the `model_provider` field across all three Codex data stores (`state_5.sqlite` threads table, `codex-dev.db` local_thread_catalog table, and session JSONL files) so historical sessions remain visible after switching providers.
- **Safe backup & restore** — every modification is automatically backed up; original values are recorded to manifests for one-command rollback (`codexsync restore`).
- **Status inspection** — `codexsync status` shows the current provider, database lock state, and session distribution across all data stores.
- **Provider management** — `codexsync providers` lists all available providers, including user-defined `[profiles.*]` from `config.toml`.
- **Built-in defaults** for OpenAI (`gpt-5.6-sol`) and DeepSeek (`deepseek-v4-pro`), overridable via Codex profiles.
- **Zero dependencies** — pure Python 3.9+ standard library.
