# Steam TUI

A high-performance headless Steam terminal launcher, library manager, and live session monitor for Linux.

Intercepts interactive terminal calls to `steam` to deliver an instantaneous, keyboard-driven `fzf` interface for browsing, launching, installing, and monitoring Steam games across all drives without loading the heavy Steam client UI.

---

## ⚡ Highlights

- **Zero-Bloat Terminal Launcher**: Typing `steam` in any terminal immediately opens an ultra-fast `fzf` browser instead of spinning up the 1GB+ CEF/Chromium Steam interface.
- **Multi-Drive Library Discovery**: Automatically traverses and indexes `libraryfolders.vdf` across all mounted drives (NVMe, SATA, Ext4, Btrfs, NTFS partitions).
- **Fast Offline Binary VDF Parser**: Reads local Steam binary caches (`appinfo.vdf` v29) and user configs to detect both installed and uninstalled owned games in milliseconds without needing network requests or API keys.
- **Kitty Terminal Art Previews**: Renders high-resolution game box art directly in Kitty (and compatible terminals) via `chafa`, along with metadata (app ID, size, status, playtime).
- **Live Session Dashboard & HUD**: Tracks running game sessions with real-time CPU, RAM, VRAM, and runtime metrics, providing interactive controls:
  - `k`: Terminate game process cleanly
  - `b`: Return to library browser while game continues in background
  - `q`: Detach monitor and exit terminal
- **Update Progress Tracker**: Automatically detects games in `[UPDATE]` or `[UPDATING]` state, displaying in-terminal download and staging progress before seamless launch.
- **Self-Healing Lock Recovery**: Automatically diagnoses and clears orphaned FIFO pipes (`steam.pipe`) and stale PID locks (`steam.pid`) that otherwise cause Steam to hang indefinitely after GUI exits.
- **Runtime Noise Filtering**: Automatically filters out Proton runtimes (Experimental, GE, Hotfix), Steam Linux Runtimes (Scout, Soldier, Sniper), Steamworks Common Redistributables, SteamVR, Soundtracks, and dedicated servers.
- **Transparent Passthrough**:
  - `steam <args>` passes through directly to `/usr/bin/steam "$@"` (e.g. `steam -shutdown`).
  - `steam --gui` summons the native Steam graphical interface.
  - Launches from desktop menus / Rofi bypass the TUI automatically.

---

## 🛠 Dependencies

- **Steam** (`steam`)
- **Python 3.8+** (`python`)
- **fzf** (`fzf`)
- **jq** (`jq`)
- **chafa** (`chafa`, for terminal image art)
- **libnotify** (`libnotify`, for desktop notifications)

### Arch Linux

```bash
sudo pacman -S --needed python fzf jq chafa libnotify steam
```

---

## 📦 Installation

Clone or copy this repository, then run the installer:

```bash
git clone https://github.com/jJohn313/steam-tui.git
cd steam-tui
./install.sh
```

The installer:
1. Verifies required dependencies.
2. Installs executables into `~/.local/bin/` (`steam` and `steam-tui-backend`).
3. Sets up `~/.config/steam_tui/config.env` and cache directories.
4. Ensures `~/.local/bin` is in your `PATH`.
5. Pre-synchronizes your Steam library cache.

---

## 🎮 Usage

### Launching

```bash
# Open interactive TUI launcher & library browser
steam

# Summon native Steam GUI directly
steam --gui

# Transparent passthrough to native Steam binary
steam -silent -applaunch 730
```

### Controls inside `fzf`

| Keybinding | Action |
| :--- | :--- |
| `<ENTER>` | **Installed Game**: Launches game and opens live session tracker.<br>**Available Game**: Prompts to install via native Steam download dialog. |
| `<Ctrl+R>` | Rescans library drives, parses manifests, refreshes cache, and live-reloads list. |
| `<ESC>` / `<Ctrl+C>` | Exits without launching Steam. |
| `Type to Filter` | Real-time fuzzy search across installed and owned games. |

### Controls in Live Session HUD

| Key | Action |
| :--- | :--- |
| `k` | Cleanly terminates the active game process. |
| `b` | Keeps game running in background and returns to library browser. |
| `q` | Detaches monitor and returns to terminal prompt. |

---

## 🔧 Backend CLI (`steam-tui-backend`)

The backend script can also be invoked directly:

```bash
# Output tab-delimited list of games for custom scripts or external pickers
steam-tui-backend --list

# Re-scan library folders and update ~/.cache/steam_tui/owned_cache.json
steam-tui-backend --sync

# Render preview card for specific AppID
steam-tui-backend --preview 1091500 INSTALLED

# Launch and attach persistent monitor to AppID
steam-tui-backend --launch-and-monitor 1091500

# Open live dashboard for already-running game
steam-tui-backend --dashboard

# Check if any Steam game is currently running
steam-tui-backend --has-running && echo "Game active"

# Focus or summon Steam GUI window
steam-tui-backend --open-gui
```

---

## ⚙️ Configuration

Custom settings live in `~/.config/steam_tui/config.env`:

```bash
# ~/.config/steam_tui/config.env

# Terminal image preview via chafa (1 to enable, 0 to disable)
ENABLE_IMAGE_PREVIEW=1

# Image preview size for chafa (Width x Height)
CHAFA_SIZE=42x11

# Optional: Provide Steam Web API Key & SteamID64 for cloud library synchronization
# STEAM_API_KEY=""
# STEAM_ID64=""
```

---

## 📂 Repository Structure

```
steam-tui/
├── bin/
│   ├── steam                  # Interactive terminal wrapper & fzf launcher
│   └── steam-tui-backend      # Core Python backend engine
├── config/
│   └── config.env.example     # Default configuration template
├── install.sh                 # One-click installer
├── .gitignore
├── LICENSE                    # MIT License
└── README.md
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
