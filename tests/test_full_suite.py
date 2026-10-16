#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for steam-tui:
1. Headless Steam Boot & CDP Interstitial Readiness (SP Desktop intact pre-launch)
2. ACF Manifest & Update Engine
3. Live Game Launch, Detection & In-Game Memory Reduction
4. Cgroup Isolation Integrity (Game NEVER trapped in steam-daemon.slice)
5. Clean Game Teardown & Deterministic 0 MB Purge
6. Download / Install Queue Pipeline
"""

import sys
import os
import time
import json
import urllib.request
import subprocess
import importlib.machinery
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_BIN = os.path.join(REPO_ROOT, "bin", "steam-tui-backend")

loader = importlib.machinery.SourceFileLoader("backend", BACKEND_BIN)
spec = importlib.util.spec_from_loader("backend", loader)
backend = importlib.util.module_from_spec(spec)
loader.exec_module(backend)

def get_cgroup_procs(slice_name):
    uid = os.getuid()
    path = f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/{slice_name}/cgroup.procs"
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                return set(f.read().strip().split())
        except Exception:
            pass
    return set()

def test_headless_boot_and_cdp():
    print("\n--- [TEST 1/5] Headless Steam Boot & Interstitial Readiness ---")
    backend.safe_post_game_shutdown()
    backend.cleanup_stale_steam_locks()
    time.sleep(1.0)

    start = time.time()
    backend.start_headless_daemon()
    boot_time = time.time() - start
    print(f"  ✔ Headless Steam ready in {boot_time:.1f}s.")

    # Check CDP JSON targets
    req = urllib.request.Request("http://127.0.0.1:8080/json", headers={"User-Agent": "steam-tui-test"})
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        targets = json.loads(resp.read().decode("utf-8"))

    has_shared_js = any("SharedJSContext" in t.get("title", "") or "SharedJSContext" in t.get("url", "") for t in targets)
    blanked_targets = [t for t in targets if t.get("url") == "about:blank"]

    print(f"  ✔ SharedJSContext Target Active: {has_shared_js}")
    print(f"  ✔ Blanked targets at boot: {len(blanked_targets)} (Expected: 0)")
    assert has_shared_js, "SharedJSContext must be active for Steamworks and cloud sync!"
    assert len(blanked_targets) == 0, "No active targets should be navigated to about:blank pre-launch!"

    # Check that the 32-bit steam daemon PID is NOT in steam-daemon.slice yet
    daemon_pids = get_cgroup_procs("steam-daemon.slice")
    res_steam = subprocess.run(["pgrep", "-x", "steam"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    steam_pids = set(res_steam.stdout.decode().split())
    overlap = daemon_pids.intersection(steam_pids)
    print(f"  ✔ Pre-launch steam-daemon.slice overlap with steam binary: {len(overlap)} (Expected: 0)")
    assert len(overlap) == 0, "steam binary must not be in steam-daemon.slice at boot so child games don't inherit it!"

def test_manifest_and_updates():
    print("\n--- [TEST 2/5] ACF Manifest Parsing & Update Pipeline ---")
    installed = backend.get_installed_games()
    print(f"  ✔ Discovered {len(installed)} installed games.")
    assert len(installed) > 0, "Should detect at least one installed game."

    # Verify manifest parser on first game
    first_app = next(iter(installed.values()))
    acf = backend.parse_acf_file(first_app["manifest_path"])
    assert acf is not None, f"Failed to parse ACF manifest at {first_app['manifest_path']}"
    assert "appid" in acf, "Parsed ACF must contain 'appid'"
    print(f"  ✔ Parsed manifest for '{acf.get('name', 'N/A')}' (StateFlags: {acf.get('state_flags')})")

def test_game_launch_and_in_game_reduction():
    print("\n--- [TEST 3/5] Live Game Launch, Cgroup Isolation & In-Game RAM Squeeze ---")
    installed = backend.get_installed_games()
    
    # Pick a fast-launching installed game (prefer 240, 413150, or first available)
    test_appid = "240" if "240" in installed else ("413150" if "413150" in installed else next(iter(installed.keys())))
    test_name = installed[test_appid]["name"]
    print(f"  Testing game launch with AppID {test_appid} ({test_name})...")

    # Launch game silently
    cmd = [backend.REAL_STEAM, "-silent", "-applaunch", str(test_appid)]
    subprocess.Popen(cmd, env=backend.get_steam_env(headless=True), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    # Poll for game window / process
    detected_game = None
    start_wait = time.time()
    while time.time() - start_wait < 30:
        time.sleep(0.5)
        g = backend.get_running_steam_game()
        if g and (str(g.get("appid")) == str(test_appid) or str(test_appid) in str(g.get("title", ""))):
            detected_game = g
            break
        # Also check reaper
        reaper = subprocess.run(["pgrep", "-f", f"AppId={test_appid}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if reaper.stdout.strip():
            detected_game = {"pid": int(reaper.stdout.decode().split()[0]), "appid": test_appid, "name": test_name}
            break

    assert detected_game is not None, f"Game {test_name} (AppID: {test_appid}) failed to launch or attach within 30s!"
    game_pid = str(detected_game["pid"])
    print(f"  ✔ Game runtime attached! PID: {game_pid}")

    # Now apply in-game surgical memory reduction
    print("  Applying in-game memory reduction (constrain_headless_cef(in_game=True))...")
    backend.constrain_headless_cef(in_game=True)
    time.sleep(1.0)

    # 1. Verify game PID is NOT inside steam-daemon.slice or steam-cef.slice
    daemon_pids = get_cgroup_procs("steam-daemon.slice")
    cef_pids = get_cgroup_procs("steam-cef.slice")
    assert game_pid not in daemon_pids, f"CRITICAL: Game PID {game_pid} is trapped inside steam-daemon.slice!"
    assert game_pid not in cef_pids, f"CRITICAL: Game PID {game_pid} is trapped inside steam-cef.slice!"
    print(f"  ✔ Cgroup Isolation Verified: Game PID {game_pid} is cleanly running outside daemon/CEF slices.")

    # 2. Verify 32-bit steam daemon PID IS in steam-daemon.slice
    res_steam = subprocess.run(["pgrep", "-x", "steam"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    steam_pids = set(res_steam.stdout.decode().split())
    assert len(daemon_pids.intersection(steam_pids)) > 0, "32-bit steam daemon PID should be in steam-daemon.slice post-launch!"
    print(f"  ✔ 32-bit steam daemon PID safely paged out inside steam-daemon.slice.")

    # 3. Check memory
    pss = backend.get_steam_pss_mb()
    print(f"  ✔ Total in-game Steam unique physical RAM: {pss} MB PSS.")

    return test_appid, game_pid

def test_game_teardown_and_purge(test_appid, game_pid):
    print("\n--- [TEST 4/5] Game Teardown & 0 MB Post-Session Purge ---")
    try:
        os.kill(int(game_pid), 9)
    except Exception:
        pass
    subprocess.run(["pkill", "-9", "-f", f"AppId={test_appid}"], stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    print("  Calling safe_post_game_shutdown()...")
    backend.safe_post_game_shutdown(test_appid)
    time.sleep(1.0)

    pss = backend.get_steam_pss_mb()
    print(f"  Post-shutdown Steam PSS: {pss} MB")
    assert pss == 0, f"Steam processes still resident post-game ({pss} MB PSS remaining)!"
    print("  ✔ Deterministic 0 MB Purge Verified.")

def test_download_pipeline():
    print("\n--- [TEST 5/5] Download / App Install Pipeline Verification ---")
    # Verify that Steam CLI accepts app installation / update queries without syntax error or crash
    backend.cleanup_stale_steam_locks()
    backend.start_headless_daemon()
    time.sleep(1.0)

    # Query Steam with app launch check for a lightweight app (Spacewar 480 or Steamworks common)
    res = subprocess.run([backend.REAL_STEAM, "-silent", "steam://install/480"], env=backend.get_steam_env(headless=True), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  ✔ steam://install/480 accepted with exit code {res.returncode}")
    assert res.returncode == 0, "Steam rejected app install URL command!"

    backend.safe_post_game_shutdown()
    time.sleep(1.0)
    assert backend.get_steam_pss_mb() == 0, "Steam failed to shut down cleanly after install test!"
    print("  ✔ Download pipeline command handled cleanly; returned to 0 MB.")

def main():
    print("\033[1;36m========================================================================\033[0m")
    print("\033[1;36m           STEAM-TUI COMPREHENSIVE END-TO-END TEST SUITE                \033[0m")
    print("\033[1;36m========================================================================\033[0m")

    try:
        test_headless_boot_and_cdp()
        test_manifest_and_updates()
        appid, pid = test_game_launch_and_in_game_reduction()
        test_game_teardown_and_purge(appid, pid)
        test_download_pipeline()

        print("\n\033[1;32m========================================================================\033[0m")
        print("\033[1;32m       ✔ ALL 5 TEST SUITES PASSED PERFECTLY (100% SUCCESS RATE)         \033[0m")
        print("\033[1;32m========================================================================\033[0m\n")
        return 0
    except Exception as e:
        print(f"\n\033[1;31m✘ TEST FAILED: {e}\033[0m\n")
        backend.safe_post_game_shutdown()
        return 1

if __name__ == "__main__":
    sys.exit(main())
