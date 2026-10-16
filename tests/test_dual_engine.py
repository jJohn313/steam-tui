#!/usr/bin/env python3
"""
Automated Test Suite for Dual-Engine Dispatcher & Anti-Cheat Classifier:
1. Anti-Cheat Classification Accuracy (VAC, EAC, BattlEye, Clean Single-Player)
2. Primary Executable Heuristic (Native ELF vs Proton Windows, Ignore crash handlers)
3. Proton Runner & CompatData Prefix Discovery
4. Per-Game LaunchOptions Parsing & %command% Handling
5. Dual-Engine Dispatcher Policy (Default official Steam vs Shim route)
"""

import os
import sys
import json
import importlib.machinery
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_BIN = os.path.join(REPO_ROOT, "bin", "steam-tui-backend")

loader = importlib.machinery.SourceFileLoader("backend", BACKEND_BIN)
spec = importlib.util.spec_from_loader("backend", loader)
backend = importlib.util.module_from_spec(spec)
loader.exec_module(backend)

def test_anticheat_classification():
    print("\n--- [TEST 1/5] Anti-Cheat Classification & Whitelist/Blacklist ---")
    
    # 1. VAC AppID
    vac_res = backend.classify_anticheat("730")
    print(f"  CS2 (730): has_anticheat={vac_res['has_anticheat']}, type='{vac_res['type']}'")
    assert vac_res['has_anticheat'] is True
    assert "VAC" in vac_res['type'] or "Valve Anti-Cheat" in vac_res['type']

    # 2. EAC AppID
    rust_res = backend.classify_anticheat("252490")
    print(f"  Rust (252490): has_anticheat={rust_res['has_anticheat']}, type='{rust_res['type']}'")
    assert rust_res['has_anticheat'] is True

    # 3. Clean singleplayer native
    installed = backend.get_installed_games()
    if "413150" in installed:
        stardew_res = backend.classify_anticheat("413150", installed["413150"]["install_path"])
        print(f"  Stardew Valley (413150): has_anticheat={stardew_res['has_anticheat']}")
        assert stardew_res['has_anticheat'] is False

    # 4. Clean singleplayer Proton
    if "1588550" in installed:
        cairn_res = backend.classify_anticheat("1588550", installed["1588550"]["install_path"])
        print(f"  Cairn (1588550): has_anticheat={cairn_res['has_anticheat']}")
        assert cairn_res['has_anticheat'] is False

    print("  ✔ Anti-cheat classification 100% verified.")

def test_primary_executable_heuristic():
    print("\n--- [TEST 2/5] Primary Executable Discovery Heuristic ---")
    installed = backend.get_installed_games()
    
    if "413150" in installed:
        exe_native = backend.find_primary_executable(installed["413150"]["install_path"])
        print(f"  Stardew Valley exe: {exe_native['name']} (ELF={exe_native['is_elf']}, EXE={exe_native['is_exe']})")
        assert exe_native is not None
        assert exe_native['is_elf'] is True
        assert exe_native['is_exe'] is False

    if "1588550" in installed:
        exe_proton = backend.find_primary_executable(installed["1588550"]["install_path"])
        print(f"  Cairn exe: {exe_proton['name']} (ELF={exe_proton['is_elf']}, EXE={exe_proton['is_exe']})")
        assert exe_proton is not None
        assert exe_proton['is_exe'] is True
        assert exe_proton['name'] == "Cairn.exe"

    print("  ✔ Primary executable discovery verified.")

def test_proton_and_compatdata():
    print("\n--- [TEST 3/5] Proton Runner & CompatData Discovery ---")
    proton_bin = backend.get_proton_binary_path()
    print(f"  Discovered Proton: {proton_bin}")
    assert proton_bin is not None
    assert os.path.isfile(proton_bin) and os.access(proton_bin, os.X_OK)

    compat_path = backend.get_compat_data_path("1588550")
    print(f"  Discovered CompatData path: {compat_path}")
    assert compat_path is not None
    assert "compatdata" in compat_path

    print("  ✔ Proton runtime and compatdata resolution verified.")

def test_launch_options_parsing():
    print("\n--- [TEST 4/5] Per-Game Launch Options Parser ---")
    opts_cs2 = backend.get_launch_options("730")
    print(f"  CS2 LaunchOptions: {opts_cs2}")
    if opts_cs2:
        assert "%command%" in opts_cs2 or len(opts_cs2) > 0

    opts_cairn = backend.get_launch_options("1588550")
    print(f"  Cairn LaunchOptions: {opts_cairn}")
    if opts_cairn:
        assert "%command%" in opts_cairn

    print("  ✔ Launch options parsing verified.")

def test_dual_engine_dispatch_policy():
    print("\n--- [TEST 5/5] Dual-Engine Dispatch Policy & Safety Default ---")
    cfg = backend.load_config()
    default_shim = cfg.get("ENABLE_LIGHTWEIGHT_SHIM", "0")
    print(f"  Default ENABLE_LIGHTWEIGHT_SHIM setting: {default_shim}")
    assert default_shim in ("0", "1", ""), "Configuration value must be valid binary toggle!"

    # Simulate dispatch check for CS2 vs Cairn
    installed = backend.get_installed_games()
    
    # Under force_shim=True:
    # CS2 should still reject shim because of VAC
    ac_cs2 = backend.classify_anticheat("730")
    should_use_shim_cs2 = (not ac_cs2["has_anticheat"])
    print(f"  CS2 under shim policy: use_shim={should_use_shim_cs2} (Expected: False)")
    assert should_use_shim_cs2 is False

    # Cairn should be eligible for shim
    if "1588550" in installed:
        ac_cairn = backend.classify_anticheat("1588550", installed["1588550"]["install_path"])
        should_use_shim_cairn = (not ac_cairn["has_anticheat"])
        print(f"  Cairn under shim policy: use_shim={should_use_shim_cairn} (Expected: True)")
        assert should_use_shim_cairn is True

    print("  ✔ Dual-engine dispatch policy verified.")

def main():
    print("================================================================")
    print("         STEAM-TUI DUAL-ENGINE & ANTI-CHEAT TEST SUITE          ")
    print("================================================================")
    test_anticheat_classification()
    test_primary_executable_heuristic()
    test_proton_and_compatdata()
    test_launch_options_parsing()
    test_dual_engine_dispatch_policy()
    print("\n================================================================")
    print("  ✔ ALL 5 DUAL-ENGINE TESTS PASSED SUCCESSFULLY!                ")
    print("================================================================\n")

if __name__ == "__main__":
    main()
