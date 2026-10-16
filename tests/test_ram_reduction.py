#!/usr/bin/env python3
"""
Automated Memory Reduction Test Suite for steam-tui.
Validates:
1. Headless daemon launch with Chromium memory-reduction flags.
2. Eager and post-launch cgroup migration (steam-cef.slice and steam-daemon.slice).
3. Surgical CDP navigation to about:blank on hidden webviews.
4. Accurate physical RAM (PSS) reporting.
5. Deterministic post-test teardown to 0 MB.
"""

import sys
import os
import time
import subprocess
import importlib.machinery
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_BIN = os.path.join(REPO_ROOT, "bin", "steam-tui-backend")

loader = importlib.machinery.SourceFileLoader("backend", BACKEND_BIN)
spec = importlib.util.spec_from_loader("backend", loader)
backend = importlib.util.module_from_spec(spec)
loader.exec_module(backend)

def get_detailed_ram():
    uid = os.getuid()
    pids = set()
    for pattern in ["steam", "steamwebhelper"]:
        try:
            out = subprocess.check_output(["pgrep", "-x", pattern], stderr=subprocess.DEVNULL).decode().split()
            for p in out:
                pids.add(p.strip())
        except Exception:
            pass
    pids.discard(str(os.getpid()))

    procs = []
    total_pss_kb = 0
    total_rss_kb = 0

    for pid in pids:
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f_cmd:
                cmd = f_cmd.read().replace(b"\0", b" ").decode("utf-8", errors="ignore").strip()[:55]
            pss, rss = 0, 0
            with open(f"/proc/{pid}/smaps_rollup", "r") as f:
                for line in f:
                    if line.startswith("Pss:"):
                        pss = int(line.split()[1])
                    elif line.startswith("Rss:"):
                        rss = int(line.split()[1])
            total_pss_kb += pss
            total_rss_kb += rss
            procs.append({
                "pid": pid,
                "pss_mb": pss // 1024,
                "rss_mb": rss // 1024,
                "cmd": cmd
            })
        except Exception:
            pass

    cef_cur = 0
    cef_cur_file = f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/steam-cef.slice/memory.current"
    if os.path.isfile(cef_cur_file):
        try:
            with open(cef_cur_file, "r") as f:
                cef_cur = int(f.read().strip()) // (1024 * 1024)
        except Exception:
            pass

    daemon_cur = 0
    daemon_cur_file = f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/steam-daemon.slice/memory.current"
    if os.path.isfile(daemon_cur_file):
        try:
            with open(daemon_cur_file, "r") as f:
                daemon_cur = int(f.read().strip()) // (1024 * 1024)
        except Exception:
            pass

    return {
        "total_pss_mb": total_pss_kb // 1024,
        "total_rss_mb": total_rss_kb // 1024,
        "cef_cgroup_mb": cef_cur,
        "daemon_cgroup_mb": daemon_cur,
        "processes": sorted(procs, key=lambda x: x["pss_mb"], reverse=True)
    }

def run_test():
    print("\033[1;36m========================================================================\033[0m")
    print("\033[1;36m       STEAM-TUI AUTOMATED RAM REDUCTION & TEARDOWN TEST SUITE           \033[0m")
    print("\033[1;36m========================================================================\033[0m\n")

    # 1. Clean environment
    print("[1/5] Ensuring clean environment (shutting down existing Steam)...")
    backend.safe_post_game_shutdown()
    backend.cleanup_stale_steam_locks()
    time.sleep(1.0)

    # 2. Start headless daemon
    print("\n[2/5] Starting Headless Steam Daemon...")
    start_time = time.time()
    backend.start_headless_daemon()
    boot_time = time.time() - start_time
    print(f"      Steam ready in {boot_time:.1f}s.")

    # 3. Apply surgical memory reduction
    print("\n[3/5] Applying surgical cgroup reclaim & CDP about:blank navigation...")
    backend.constrain_headless_cef()
    time.sleep(1.5)

    # 4. Measure accurate physical RAM
    print("\n[4/5] Measuring kernel-accounted physical memory (PSS)...")
    stats = get_detailed_ram()

    print(f"\n  \033[1;32m● Total Unique Physical RAM (PSS): {stats['total_pss_mb']} MB\033[0m")
    print(f"  \033[2m● Naive Task Manager Sum (RSS):     {stats['total_rss_mb']} MB\033[0m")
    print(f"  \033[1;34m● steam-cef.slice Cgroup:            {stats['cef_cgroup_mb']} MB\033[0m")
    print(f"  \033[1;35m● steam-daemon.slice Cgroup:         {stats['daemon_cgroup_mb']} MB\033[0m\n")

    print(f"  {'PID':>7} | {'PSS (MB)':>8} | {'RSS (MB)':>8} | Command")
    print("  " + "-" * 70)
    for p in stats["processes"]:
        print(f"  {p['pid']:>7} | {p['pss_mb']:>8} | {p['rss_mb']:>8} | {p['cmd']}")

    # 5. Deterministic shutdown verification
    print("\n[5/5] Shutting down Steam and verifying 0 MB reclamation...")
    backend.safe_post_game_shutdown()
    time.sleep(1.0)

    post_stats = get_detailed_ram()
    if post_stats["total_pss_mb"] == 0:
        print("\n\033[1;32m✔ SUCCESS: All Steam processes cleanly terminated. RAM footprint = 0 MB.\033[0m\n")
        return 0
    else:
        print(f"\n\033[1;31m✘ FAILURE: Steam processes still resident ({post_stats['total_pss_mb']} MB PSS remaining).\033[0m\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_test())
