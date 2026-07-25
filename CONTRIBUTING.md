# Contributing to codexsync

Thanks for your interest in contributing! This project aims to solve a real pain point for Codex users, and community contributions are essential to making it better.

## Ways to Contribute

- **Report bugs** — Found something broken? Open an [issue](https://github.com/zssggle-rgb/codexsync/issues).
- **Suggest features** — Have an idea? We'd love to hear it.
- **Improve docs** — Typos, clarifications, translations — all welcome.
- **Submit code** — Fix a bug or build a feature (see below).
- **Share the project** — A star or a tweet helps more than you think.

## Development Setup

```bash
git clone https://github.com/zssggle-rgb/codexsync.git
cd codexsync

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Verify it works
codexsync status
```

## Code Style

- **Python 3.9+** — use `from __future__ import annotations` for forward references.
- **Zero dependencies** — only the standard library. If you need a third-party package, discuss it in an issue first.
- **Type hints** — all public functions should have type annotations.
- **Docstrings** — every module and public function needs a docstring.
- **Line length** — 100 characters max (enforced by ruff config in `pyproject.toml`).

## Pull Request Process

1. **Fork** the repo and create a branch: `git checkout -b feat/my-feature`
2. **Write code** following the style above
3. **Test** your changes against a real Codex installation if possible
4. **Commit** with a clear message (see conventions below)
5. **Open a PR** — fill out the template and link any related issues

### Commit Message Convention

```
<type>: <short description>

<optional longer description>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
- `feat: add Anthropic provider support`
- `fix: handle missing sessions directory gracefully`
- `docs: add Linux installation instructions`

## Project Structure

```
codexsync/
├── codexsync/          # Python package
│   ├── __init__.py     # Version info
│   ├── __main__.py     # python -m codexsync entry
│   ├── cli.py          # Command-line interface
│   ├── config.py       # config.toml read/patch
│   ├── sync.py         # Session provider sync (3 data stores)
│   ├── switcher.py     # Full switch workflow
│   └── constants.py    # Paths & built-in defaults
├── scripts/
│   └── install.sh      # One-line installer
├── tests/
├── pyproject.toml
└── README.md
```

## Questions?

Open an [issue](https://github.com/zssggle-rgb/codexsync/issues) with the `question` label — we'll help you out.
