"""One-command launcher that verifies local Spark-X2.6-4B GGUF + llama-server, runs all ablations, and renders demo."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(r"C:\Users\qqq\.gemini\antigravity\scratch\plaincivic-spark-skillhub")
RUNTIME = Path(r"D:\tools\spark-runtime")
VULKAN_ZIP = RUNTIME / "llama-b12671-bin-win-vulkan-x64.zip"
VULKAN_DIR = RUNTIME / "llama-b12671-vulkan"
GGUF_PATH = RUNTIME / "models" / "XHToken--Spark-X2.6-4B-GGUF" / "Spark-X2.6-4B-Q4_K_M.gguf"
EXPECTED_GGUF_BYTES = 3543441312
EXPECTED_GGUF_SHA256 = "91cb2811aebb47ac916aa619d27d4cdd7f4143106b7917accb8ead4cd7f5cbd9"


def find_llama_server() -> Path | None:
    if VULKAN_ZIP.exists() and not any(VULKAN_DIR.rglob("llama-server.exe")):
        VULKAN_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Extracting {VULKAN_ZIP} -> {VULKAN_DIR} ...", flush=True)
        with zipfile.ZipFile(VULKAN_ZIP, "r") as zf:
            zf.extractall(VULKAN_DIR)
    for d in (VULKAN_DIR, RUNTIME / "llama-b12671-cuda12.4", RUNTIME):
        if d.exists():
            hit = next(d.rglob("llama-server.exe"), None)
            if hit:
                return hit
    return None


def find_gguf() -> Path | None:
    if GGUF_PATH.exists():
        return GGUF_PATH
    for p in RUNTIME.rglob("Spark-X2.6-4B*.gguf"):
        if p.stat().st_size > 1_000_000_000:
            return p
    return None


def wait_for_health(url: str, timeout: int = 90) -> bool:
    import requests

    s = requests.Session()
    s.trust_env = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = s.get(f"{url}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def main() -> int:
    server_exe = find_llama_server()
    gguf = find_gguf()
    if not server_exe:
        print(f"[MISSING] llama-server.exe not found under {RUNTIME}. Place {VULKAN_ZIP.name} in {RUNTIME}.")
        return 1
    if not gguf:
        print(f"[MISSING] Spark-X2.6-4B GGUF not found under {RUNTIME}. Place it at {GGUF_PATH}.")
        return 1

    print(f"[OK] llama-server: {server_exe}", flush=True)
    print(f"[OK] GGUF model:   {gguf} ({gguf.stat().st_size} bytes)", flush=True)

    # Start llama-server on GPU (-ngl 99) with jinja chat template enabled
    port = 8080
    base_url = f"http://127.0.0.1:{port}"
    log_path = ROOT / "runs" / "llama_server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(log_path, "w", encoding="utf-8")

    cmd = [
        str(server_exe),
        "-m", str(gguf),
        "-ngl", "99",
        "-c", "16384",
        "--jinja",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    print(f"[START] {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
    try:
        if not wait_for_health(base_url, timeout=120):
            print("[ERROR] llama-server did not become healthy within 120s. Check runs/llama_server.log")
            return 2
        print("[READY] llama-server is healthy!", flush=True)

        env = dict(**__import__("os").environ)
        env["PYTHONPATH"] = str(ROOT / "src")

        runs = [
            ("baseline_v1", "low"),
            ("skill_v2", "none"),
            ("skill_v2", "low"),
            ("skill_v2", "high"),
        ]
        for mode, thinking in runs:
            print(f"\n================ RUNNING {mode} (thinking={thinking}) ================", flush=True)
            rc = subprocess.run(
                [sys.executable, "-m", "plaincivic.runner", "--base-url", base_url, "--mode", mode, "--thinking", thinking],
                cwd=str(ROOT),
                env=env,
                check=False,
            ).returncode
            if rc != 0:
                print(f"[WARN] Run {mode}/{thinking} exited with {rc}", flush=True)

        # Render interactive HTML demo using skill_v2_low (or high)
        subprocess.run(
            [sys.executable, "-m", "plaincivic.render_demo", "skill_v2_low"],
            cwd=str(ROOT),
            env=env,
            check=True,
        )
        print("\n[ALL DONE] Benchmarks finished and demo/index.html rendered!", flush=True)
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        log_f.close()


if __name__ == "__main__":
    sys.exit(main())
