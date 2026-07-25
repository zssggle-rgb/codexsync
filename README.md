<div align="center">

# codexsync

**Seamlessly switch Codex model providers without losing session history.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://support.apple.com/macos)
[![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-green.svg)](https://github.com/zssggle-rgb/codexsync)

[English](#english) · [中文](#中文)

</div>

---

# English

## The Problem

When you change the `model_provider` in Codex's `config.toml` (e.g. switching from OpenAI to DeepSeek), **all your historical sessions disappear from the desktop sidebar**. The data isn't lost — Codex filters sessions by a `model_provider` field and hides anything that doesn't match the current provider.

If you switch providers frequently, you're forced to maintain **two separate session histories**, or dig through raw JSONL files on disk.

## The Solution

`codexsync` synchronises the `model_provider` field across **all three** places Codex stores it, so every session stays visible no matter which provider is active. **One session history, any provider.**

```
~/.codex/
├── state_5.sqlite              ← threads table (desktop task list)
├── sqlite/codex-dev.db         ← local_thread_catalog table
└── sessions/**/*.jsonl         ← each file's session_meta payload
         │
         ▼
   codexsync syncs ALL THREE to the current provider
         │
         ▼
   ✅ All sessions visible in the sidebar
```

## Features

- **One-command switch** — `codexsync switch deepseek` edits config, quits the app, syncs sessions, and relaunches — automatically.
- **No data loss** — every modification is backed up; original values are saved to manifests for instant rollback.
- **Zero dependencies** — pure Python 3.9+ standard library. No `pip install` needed.
- **Safe by design** — detects database locks and refuses to run while the app is open.
- **Extensible** — built-in defaults for OpenAI & DeepSeek, plus automatic detection of user-defined `[profiles.*]` in `config.toml`.

## Quick Start

### Install

```bash
# Option 1: One-line install (recommended)
curl -fsSL https://raw.githubusercontent.com/zssggle-rgb/codexsync/main/scripts/install.sh | bash

# Option 2: pip install from source
git clone https://github.com/zssggle-rgb/codexsync.git
cd codexsync
pip install -e .
```

### Usage

```bash
# See what's currently active
codexsync status

# Switch to DeepSeek (auto: edit config → quit app → sync → relaunch)
codexsync switch deepseek

# Switch back to OpenAI
codexsync switch openai

# Sync sessions to current provider without changing config
codexsync sync

# Undo the last sync
codexsync restore

# List available providers
codexsync providers
```

## Command Reference

| Command | Description |
|---------|-------------|
| `codexsync status` | Show current provider, database lock state, and session distribution |
| `codexsync switch <provider>` | Switch to a provider (edits config, restarts app, syncs sessions) |
| `codexsync sync` | Sync all sessions to the current provider (no config change) |
| `codexsync restore` | Roll back to the pre-sync state using saved manifests |
| `codexsync providers` | List all available providers (built-in + profiles) |

## How It Works

Codex stores session metadata in **three** locations, each tagged with a `model_provider` field:

1. **`~/.codex/state_5.sqlite`** → `threads` table — the primary source for the desktop app's task/session list.
2. **`~/.codex/sqlite/codex-dev.db`** → `local_thread_catalog` table — source for the project directory view.
3. **`~/.codex/sessions/**/*.jsonl`** → each file's first line is a `session_meta` record with `payload.model_provider`.

When you switch providers, `codexsync` updates all three to match, so the desktop app shows every session regardless of which provider created it.

> **Note:** Syncing makes old sessions *visible and browsable*. Resuming (continuing) a session originally built for OpenAI under DeepSeek may hit format incompatibilities — browsing and searching history is always safe.

## FAQ

**Q: Will this delete or corrupt my sessions?**

No. `codexsync` only modifies the `model_provider` metadata field. The conversation content in JSONL files is never touched. Every change is backed up automatically.

**Q: Do I need to quit Codex before running?**

`codexsync switch` handles this automatically. If you run `codexsync sync` manually, you must quit the app first — the script will detect the database lock and tell you.

**Q: Can I add custom providers?**

Yes. Add a `[profiles.myprovider]` section to your `~/.codex/config.toml` with `model` and `model_provider` keys. It will appear in `codexsync providers` and work with `codexsync switch myprovider`.

**Q: Does this work with Codex CLI?**

The session sync works for both desktop and CLI. The auto-restart feature (`switch` command) targets the desktop app; CLI users should run `codexsync sync` after changing `config.toml`.

## Roadmap

- [ ] Homebrew formula (`brew install codexsync`)
- [ ] Support for more providers (Anthropic, Moonshot, Qwen, etc.)
- [ ] `codexsync export` — export sessions as Markdown/JSON
- [ ] `codexsync import` — import context from Claude Code / Cursor
- [ ] TUI panel for browsing, searching, and restoring sessions
- [ ] Windows & Linux support
- [ ] Multi-device config sync

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) © 2026 zssggle-rgb

---

# 中文

## 问题

在 Codex 的 `config.toml` 中切换 `model_provider`（比如从 OpenAI 切到 DeepSeek）后，**桌面端侧边栏的历史会话全部消失**。数据没有丢失——Codex 按 `model_provider` 字段过滤，隐藏了不匹配当前 provider 的 session。

如果频繁切换 provider，你要么维护两套 session 历史，要么去磁盘翻原始 JSONL 文件。

## 解决方案

`codexsync` 把 `model_provider` 字段在 Codex 存储它的**全部三处**同步统一，让所有 session 不管用哪个 provider 都始终可见。**一套 session 历史，任意 provider 切换。**

## 核心功能

- **一键切换** — `codexsync switch deepseek` 自动完成：改配置 → 关闭 app → 同步 session → 重开
- **零数据丢失** — 每次修改自动备份，原始值记录到 manifest，一键还原
- **零依赖** — 纯 Python 3.9+ 标准库，无需 pip install
- **安全设计** — 检测数据库锁，app 运行时拒绝修改并提示
- **可扩展** — 内置 OpenAI/DeepSeek 默认值，自动识别 config.toml 中的 `[profiles.*]` 自定义 provider

## 快速开始

```bash
# 安装
curl -fsSL https://raw.githubusercontent.com/zssggle-rgb/codexsync/main/scripts/install.sh | bash

# 切到 DeepSeek（全自动）
codexsync switch deepseek

# 切回 OpenAI
codexsync switch openai

# 查看状态
codexsync status
```

## 命令一览

| 命令 | 说明 |
|------|------|
| `codexsync status` | 查看当前 provider、数据库锁状态、session 分布 |
| `codexsync switch <provider>` | 切换 provider（改配置 + 重启 app + 同步 session） |
| `codexsync sync` | 仅同步 session 到当前 provider（不改配置） |
| `codexsync restore` | 还原到上次同步前的状态 |
| `codexsync providers` | 列出所有可用 provider |

## 工作原理

Codex 在**三处**存储 session 元数据，每处都标记了 `model_provider`：

1. **`state_5.sqlite`** 的 `threads` 表 — 桌面端任务列表的数据源
2. **`codex-dev.db`** 的 `local_thread_catalog` 表 — 项目目录视图的数据源
3. **`sessions/**/*.jsonl`** 每个文件首行的 `session_meta` 记录

切换 provider 时，`codexsync` 把这三处全部更新为当前 provider，桌面端就会显示所有 session。

> **注意：** 同步后旧 session 可以**浏览和搜索**。如果要 resume（续聊）OpenAI 时期创建的 session，DeepSeek 可能对部分消息格式不完全兼容——浏览历史始终安全。

## 贡献

欢迎提交 Issue 和 PR！参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE) © 2026 zssggle-rgb
