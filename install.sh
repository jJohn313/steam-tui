#!/usr/bin/env bash
# ==============================================================================
# Steam TUI - Headless Steam Terminal Launcher & Library Manager Installer
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_SRC="${SCRIPT_DIR}/bin"
CFG_SRC="${SCRIPT_DIR}/config"

TARGET_BIN="${HOME}/.local/bin"
TARGET_CFG="${HOME}/.config/steam_tui"
TARGET_CACHE="${HOME}/.cache/steam_tui"

echo "======================================================================"
echo "  🚀 Installing Headless Steam Terminal Launcher & Library Manager"
echo "======================================================================"

# 1. Dependency Resolution
REQUIRED_PKGS=("python" "fzf" "jq" "chafa" "libnotify" "steam")
MISSING_PKGS=()

for pkg in "${REQUIRED_PKGS[@]}"; do
    case "$pkg" in
        "libnotify")
            command -v notify-send >/dev/null 2>&1 || MISSING_PKGS+=("$pkg")
            ;;
        *)
            command -v "$pkg" >/dev/null 2>&1 || MISSING_PKGS+=("$pkg")
            ;;
    esac
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo "📦 Missing required dependencies: ${MISSING_PKGS[*]}"
    if command -v pacman >/dev/null 2>&1; then
        echo "🔧 Installing via pacman (requires sudo)..."
        sudo pacman -S --needed --noconfirm "${MISSING_PKGS[@]}"
    else
        echo "⚠️ Warning: pacman not found. Please install manually: ${MISSING_PKGS[*]}"
    fi
else
    echo "✅ All dependencies satisfied (python, fzf, jq, chafa, libnotify, steam)."
fi

# 2. Setup Target Directories
echo "📁 Setting up user directories..."
mkdir -p "$TARGET_BIN"
mkdir -p "$TARGET_CFG"
mkdir -p "$TARGET_CACHE"

# 3. Install Executables
echo "⚙️  Installing binaries to $TARGET_BIN..."
cp -f "${BIN_SRC}/steam" "${TARGET_BIN}/steam"
cp -f "${BIN_SRC}/steam-tui-backend" "${TARGET_BIN}/steam-tui-backend"
chmod +x "${TARGET_BIN}/steam"
chmod +x "${TARGET_BIN}/steam-tui-backend"

# 4. Install Default Configuration Template
if [ ! -f "${TARGET_CFG}/config.env" ]; then
    echo "📝 Creating initial configuration at ${TARGET_CFG}/config.env..."
    if [ -f "${CFG_SRC}/config.env.example" ]; then
        cp "${CFG_SRC}/config.env.example" "${TARGET_CFG}/config.env"
    fi
else
    echo "ℹ️  Existing configuration found at ${TARGET_CFG}/config.env (preserving)."
fi

# 5. Ensure ~/.local/bin is in PATH
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
for rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
    if [ -f "$rc" ]; then
        if ! grep -q '\.local/bin' "$rc"; then
            echo "🔧 Adding ~/.local/bin to PATH in $rc..."
            echo -e "\n# User local binaries\n$PATH_LINE" >> "$rc"
        fi
    fi
done

# 6. Initial Cache Synchronization
echo "🔄 Running initial Steam library sync..."
if [ -d "${HOME}/.local/share/Steam" ]; then
    "${TARGET_BIN}/steam-tui-backend" --sync || true
    echo "✅ Library cache populated at $TARGET_CACHE"
else
    echo "ℹ️  Steam directory (~/.local/share/Steam) not found yet. Run 'steam-tui-backend --sync' after logging into Steam."
fi

echo ""
echo "======================================================================"
echo "  🎉 Installation Complete!"
echo "======================================================================"
echo "  • Run 'steam' in any terminal to open the interactive TUI."
echo "  • Run 'steam <args>' to pass through to native Steam directly."
echo "  • Run 'steam --gui' to summon native Steam GUI."
echo "  • Hit <Ctrl+R> inside the fzf launcher to refresh your library cache."
echo "======================================================================"
