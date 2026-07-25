#!/usr/bin/env bash
# codexsync installer — one-line install for macOS
# Usage: curl -fsSL .../install.sh | bash
set -e

CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
INSTALL_DIR="$HOME/.codex"
SCRIPT_NAME="codexsync"
SRC_URL="https://raw.githubusercontent.com/zssggle-rgb/codexsync/main/codexsync"

echo "codexsync installer"
echo "==================="
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required but not found."
    echo "Install it from https://www.python.org/downloads/"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python: $PY_VERSION"

# Check Codex directory
if [ ! -d "$CODEX_DIR" ]; then
    echo "Warning: Codex directory ($CODEX_DIR) not found."
    echo "         codexsync will still be installed but won't work until Codex is set up."
fi

# Download package files
echo ""
echo "Downloading codexsync..."
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

for f in __init__.py __main__.py cli.py config.py sync.py switcher.py constants.py; do
    curl -fsSL "$SRC_URL/$f" -o "$TMP_DIR/$f" || {
        echo "Error: failed to download $f"
        exit 1
    }
done

# Install to ~/.codex/codexsync/
PKG_DIR="$INSTALL_DIR/codexsync"
mkdir -p "$PKG_DIR"
cp "$TMP_DIR"/*.py "$PKG_DIR/"

# Create wrapper script
WRAPPER="$INSTALL_DIR/codexsync-cli"
cat > "$WRAPPER" << EOF
#!/bin/bash
exec python3 "$PKG_DIR/__main__.py" "\$@"
EOF
chmod +x "$WRAPPER"

# Add alias to shell config
SHELL_RC=""
case "$SHELL" in
    */zsh) SHELL_RC="$HOME/.zshrc" ;;
    */bash) SHELL_RC="$HOME/.bashrc" ;;
esac

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "codexsync-cli" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# codexsync" >> "$SHELL_RC"
        echo "alias codexsync=\"$WRAPPER\"" >> "$SHELL_RC"
        echo "Added alias to $SHELL_RC"
    else
        echo "Alias already exists in $SHELL_RC"
    fi
fi

echo ""
echo "Installation complete!"
echo ""
echo "Open a new terminal window, then run:"
echo "  codexsync status"
echo ""
echo "To switch providers:"
echo "  codexsync switch deepseek"
echo "  codexsync switch openai"
