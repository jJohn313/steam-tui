# Steam TUI

A high-performance headless Steam terminal launcher, library manager, and live session monitor for Linux.

Intercepts interactive terminal calls to `steam` to deliver an instantaneous, keyboard-driven `fzf` interface for browsing, launching, installing, and monitoring Steam games across all drives without loading the heavy Steam client UI.

---

## ⚡ Highlights

- **Dual-Engine Architecture (Zero-Overhead Shim vs. Headless Steam)**: Automatically evaluates game requirements to select the optimal engine. Singleplayer and offline games run directly through an emulated compatibility shim with **0 MB Steam client RAM overhead**, while titles requiring online anti-cheat or official Valve DRM route safely through the headless client.
- **Intelligent Anti-Cheat Classifier & Safety Fallback**: Proactively inspects game binaries (`magic`, `machine_type`, `.bind` section signatures) to detect VAC, Easy Anti-Cheat (EAC), BattlEye, Denuvo, Ricochet, Vanguard, and Valve SteamStub DRM. Guaranteed zero bans or launch crashes by automatically promoting protected titles to the official Steam runtime.
- **100% Bidirectional Save Data & Cloud Storage Synchronization**: Dynamically detects your active Steam credentials (`SteamID64`, persona name, 32-bit `AccountID`) from `loginusers.vdf` and synchronizes user profiles into Proton prefixes and native directories. Automatically symlinks `<appid>/remote` directly to Valve's official `userdata/<account_id>/<appid>/remote/`, guaranteeing that save files (including SteamID-partitioned saves like *NieR Replicant* or Capcom games) and Steam Cloud saves are shared transparently across both modes.
- **In-Flight Update Tracking & Automatic Game Launch**: Intercepts active game downloads and updates at launch time, rendering live progress bars, download speeds, and ETAs in the terminal without opening the GUI, and automatically launches the game the moment the update completes.
- **Low-RAM Headless Daemon Diet**: Starts Steam silently with `-silent`, `-nofriendsui`, `-nochatui`, `-cef-disable-gpu`, `-cef-disable-gpu-compositing`, `-cef-in-process-gpu`, `-cef-enable-debugging`, and `-js-flags=--max-old-space-size=96` to collapse helper processes and cap V8 heap growth while keeping `SharedJSContext` responsive for Steam Input, overlay, achievements, and cloud sync.
- **Surgical In-Game CEF Memory Reducer**: Once a game attaches, `constrain_headless_cef()` isolates `steamwebhelper` PIDs into a dedicated background cgroup slice (`steam-cef.slice`) with `MemoryHigh=128M` (with NO `MemoryMax` so OOM never kills) and triggers kernel `memory.reclaim`, while purging non-SharedJSContext hidden CEF tabs via local CDP. This drives idle Chromium physical memory down to ~80–120 MB without trapping the game process or breaking Steam Input.
- **Deterministic Post-Game RAM Reclamation (0 MB Idle)**: When a game exits, the backend waits for the Proton `reaper` container and `wineserver` to exit cleanly, confirms Steam Cloud sync completion via `cloud_log.txt`, verifies no background updates are active, and automatically runs `steam -shutdown`.
- **Detached Background Auto-Shutdown**: Pressing `q` or `Esc` in the HUD detaches the terminal while spawning a background watcher (`--auto-shutdown <appid>`) that automatically performs the safe cloud sync flush and shutdown when the game closes.
- **Automatic GUI RAM Reclamation**: Running `steam --gui` launches the full Store/Community client, monitors the Hyprland window lifecycle, and automatically shuts down CEF processes when the window is closed to immediately recover 1GB+ of system memory.
- **Headless Terminal Installation & EULA Bypass**: Installs games directly from terminal via bootstrap ACF manifests and `steam://install/<appid>`, bypassing GUI prompts, multi-step install modals, and EULA blocks.
- **Interactive Multi-Drive Target Selector**: Prompts for target library destination when installing across multiple mounted drives with free disk space statistics.
- **Real-Time Speed & Progress Tracking**: Reads live download throughput directly from Steam's `content_log.txt` (with ACF fallback), computing ETA and staging states.
- **Non-Steam Games & Modded Shortcuts**: Parses binary `shortcuts.vdf` to seamlessly integrate custom executables and modded wrappers into your library, computing 64-bit shortcut IDs to launch via Proton alongside native titles.
- **In-TUI Launch Options Editor (`Ctrl-O`)**: Reads and edits `LaunchOptions` (e.g. `gamemoderun %command%` or `PROTON_ENABLE_NVAPI=1 %command%`) directly in `localconfig.vdf` without opening the GUI.
- **Proton Version & Compatibility Selector (`Ctrl-P`)**: Scans system and user compatibility directories (Proton Experimental, GE-Proton, Proton Hotfix, etc.) and writes per-game mappings into `config.vdf`.
- **Direct Prefix & Save-Data Manager (`Ctrl-F`)**: Instant shortcut menu to open game directories, browse Proton prefixes (`drive_c`), jump to Windows `AppData` save paths, or launch `winecfg`.
- **Cloud Sync & Runtime Preview**: Previews show Proton compatibility tool mapping and last Cloud save synchronization timestamp.
- **Robust v28/v29 Binary `appinfo.vdf` Parser**: Handles Steam client schema changes (16-byte headers, 68-byte entry headers, and string table index resolution) for instantaneous name and metadata lookups with zero network calls.
- **Process Group Termination**: Terminating a game signals the entire process group and reaper tree (`AppId=<appid>`), preventing hanging wineserver or anti-cheat helpers.
- **Pixel-Perfect Kitty Terminal Art**: Renders true-color box art directly in Kitty via `chafa -f kitty` or `kitten icat`, with automatic fallback to Steam CDN caching for uninstalled titles.
- **Live Session Dashboard & HUD**: Tracks running game sessions with real-time CPU, RAM, VRAM, and runtime metrics, providing interactive controls:
  - `k`: Terminate game process group cleanly
  - `b`: Return to library browser while game continues in background
  - `q`: Detach monitor and exit terminal
- **Terminal Uninstallation**: Press `Ctrl-X` inside `fzf` to cleanly dispatch `+app_uninstall` without touching the GUI.
- **Self-Healing Lock Recovery**: Automatically diagnoses and clears orphaned FIFO pipes (`steam.pipe`) and stale PID locks (`steam.pid`) that otherwise cause Steam to hang indefinitely after GUI exits.
- **Vanilla & Millennium Compatible**: Fully compatible with standard vanilla Steam as well as Millennium Steam client mods. Automatically detects and preserves `MILLENNIUM_RUNTIME_PATH` to prevent `libXtst.so.6` crash loops while remaining 100% zero-config and dependency-free for stock Steam users.
- **Transparent Passthrough**:
  - `steam <args>` passes through directly to `/usr/bin/steam "$@"`.
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
