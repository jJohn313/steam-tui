# Steam TUI

A high-performance headless Steam terminal launcher, library manager, and live session monitor for Linux.

Intercepts interactive terminal calls to `steam` to deliver an instantaneous, keyboard-driven `fzf` interface for browsing, launching, installing, and monitoring Steam games across all drives without loading the heavy Steam client UI.

---

## ⚡ Highlights

### 🚀 Dual-Engine Architecture & 0 MB Shim
- **Zero-Overhead Compatibility Shim**: Launches singleplayer and offline games with **0 MB Steam client RAM overhead** — bypasses Chromium, CEF, and background daemons entirely.
- **Intelligent Anti-Cheat Classifier**: Inspects binary headers (`magic`, `machine_type`, `.bind`) for VAC, EAC, BattlEye, Denuvo, and SteamStub DRM, routing protected titles safely to official Steam.
- **100% Shared Saves & Cloud Sync**: Automatically inherits your active SteamID64, persona, and 32-bit AccountID. Symlinks Remote Storage directly into Valve's official Cloud save directories.
- **In-Flight Update Interception**: Catches active game updates at launch, renders live progress bars and ETAs in the terminal, and auto-launches the game the moment the download finishes.

### 🧠 Surgical Resource Management
- **Low-RAM Headless Daemon**: When official Steam is required, runs stripped (`-silent -nofriendsui -nochatui`) with cgroup memory isolation (`steam-cef.slice`) and CDP tab purging (~80–120 MB RAM vs 1.2 GB+ GUI).
- **True 0 MB Post-Game Reclamation**: Flushes cloud saves, waits for wineserver/reaper containers to exit, and automatically terminates background helper daemons.
- **Auto GUI Memory Recovery**: `steam --gui` summons the full desktop client and automatically cleans up Chromium/CEF processes when the window closes to reclaim 1 GB+ of RAM.

### 🎮 Keyboard-Driven Terminal Power
- **Instant FZF Launcher**: Lightning-fast fuzzy search across all libraries, secondary drives, and non-Steam shortcuts with Kitty true-color box art preview.
- **In-TUI Settings & Prefix Manager**: Inline launch options editor (`Ctrl-O`), Proton compatibility switcher (`Ctrl-P`), and direct prefix/save directory manager (`Ctrl-F`).
- **Headless Installation & EULA Bypass**: Install games across target drives via terminal without webview prompts or multi-step wizard modals.
- **Live Session Dashboard & HUD**: Real-time CPU, RAM, VRAM, and runtime tracking with interactive session controls (`k` to kill, `b` to background, `q` to detach).
- **Terminal Uninstallation**: Press `Ctrl-X` inside `fzf` to cleanly dispatch `+app_uninstall` without touching the GUI.
- **Self-Healing Lock Recovery**: Automatically diagnoses and clears orphaned FIFO pipes (`steam.pipe`) and stale PID locks (`steam.pid`) on startup.
- **Vanilla & Millennium Compatible**: Fully compatible with standard vanilla Steam as well as Millennium Steam client mods.
- **Transparent Passthrough**: Standard Steam CLI arguments (`steam -applaunch`), desktop menus, and Rofi/dmenu shortcuts pass through seamlessly.
  - `steam --gui` summons the native Steam graphical interface.

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
| `<ENTER>` | **Auto Launch**: Automatically selects optimal engine (0 MB Shim for singleplayer/offline vs Headless Steam for anti-cheat/DRM), tracks in-flight updates, and launches game.<br>**Shortcut**: Launches non-Steam shortcut via Proton.<br>**Available Game**: Triggers terminal install with drive selector and EULA bypass. |
| `<Ctrl+S>` | **Force Official Steam**: Launches selected game using headless official Steam client (bypasses 0 MB shim). |
| `<Ctrl+Z>` | **Force 0 MB Shim**: Launches selected game using lightweight compatibility shim (zero Steam client overhead). |
| `<Ctrl+I>` | Filters view to display **Installed, Updating, & Shortcut games only**. |
| `<Ctrl+A>` | Resets filter to show **All games** (installed + uninstalled + shortcuts). |
| `<Ctrl+O>` | Opens inline editor for per-game **Launch Options** (`localconfig.vdf`). |
| `<Ctrl+P>` | Selects Proton / GE-Proton **Compatibility Tool** (`config.vdf`). |
| `<Ctrl+F>` | Opens **Prefix & Files Menu** (game dir, prefix `drive_c`, `AppData`, `winecfg`, and **Save Data Sync**). |
| `<Ctrl+X>` | Prompts to **Uninstall selected game** directly from terminal. |
| `<Ctrl+R>` | Rescans library drives, parses manifests, refreshes cache, and live-reloads list. |
| `<ESC>` / `<Ctrl+C>` | Exits launcher without starting Steam. |
| `Type to Filter` | Real-time fuzzy search across installed, shortcut, and owned games. |

### Controls in Live Session HUD

| Key | Action |
| :--- | :--- |
| `k` | Cleanly terminates the active game process group and Proton runtimes. |
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

# Launch and attach persistent monitor to AppID (automatic dual-engine dispatch)
steam-tui-backend --launch-and-monitor 1091500

# Force launch with specific engine (--shim for 0 MB client, --official for Valve client)
steam-tui-backend --launch-and-monitor 1091500 --shim
steam-tui-backend --launch-and-monitor 1091500 --official

# Inspect anti-cheat & DRM compatibility classification
steam-tui-backend --inspect-anticheat 1091500

# Synchronize & share save data & cloud storage symlinks across all games (or specify AppID)
steam-tui-backend --sync-saves
steam-tui-backend --sync-saves 1091500

# Open interactive launch options editor
steam-tui-backend --edit-launch-options 1091500

# Open interactive Proton compatibility tool selector
steam-tui-backend --set-proton 1091500

# Open prefix and files navigation menu (with save sync)
steam-tui-backend --files-menu 1091500

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

# Dual-Engine Architecture Settings
# 1 = Use 0 MB lightweight compatibility shim for singleplayer/offline games
# 0 = Always route through headless official Steam client
ENABLE_LIGHTWEIGHT_SHIM=1

# 1 = Force official Steam client globally for all launches
# 0 = Allow intelligent anti-cheat classifier to choose the optimal engine
FORCE_OFFICIAL_STEAM=0

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
