"""One-command launcher that runs all 4 ablations with exact llama-server --reasoning-budget controls and renders demo."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("SPARK_RUNTIME_DIR", r"D:\tools\spark-runtime"))  # override with SPARK_RUNTIME_DIR
VULKAN_ZIP = RUNTIME / "llama-b12671-bin-win-vulkan-x64.zip"
VULKAN_DIR = RUNTIME / "llama-b12671-vulkan"
GGUF_PATH = RUNTIME / "models" / "XHToken--Spark-X2.6-4B-GGUF" / "Spark-X2.6-4B-Q4_K_M.gguf"


def find_llama_server() -> Path | None:
    if VULKAN_ZIP.exists() and not any(VULKAN_DIR.rglob("llama-server.exe")):
        VULKAN_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(VULKAN_ZIP, "r") as zf:
            zf.extractall(VULKAN_DIR)
    for d in (VULKAN_DIR, RUNTIME):
        if d.exists():
            hit = next(d.rglob("llama-server.exe"), None)
            if hit:
                return hit
    return None


def wait_for_health(url: str, timeout: int = 90) -> bool:
    s = requests.Session()
    s.trust_env = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if s.get(f"{url}/health", timeout=3).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1.0)
    return False


def run_with_server(
    server_exe: Path,
    gguf: Path,
    mode: str,
    thinking: str,
    reasoning_budget: int,
    port: int,
    cases_arg: str = "",
    resume: bool = True,
) -> int:
    base_url = f"http://127.0.0.1:{port}"
    log_path = ROOT / "runs" / f"llama_server_{mode}_{thinking}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(log_path, "w", encoding="utf-8")

    cmd = [
        str(server_exe),
        "-m", str(gguf),
        "-ngl", "99",
        "-c", "16384",
        "--jinja",
        "--reasoning", "off" if thinking == "none" else "on",
        "--reasoning-budget", str(reasoning_budget),
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    if thinking in {"low", "high"}:
        cmd.extend(["--reasoning-effort", thinking])

    print(f"\n================ STARTING {mode} (thinking={thinking}, budget={reasoning_budget}) ================", flush=True)
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
    try:
        if not wait_for_health(base_url, timeout=90):
            print(f"[ERROR] llama-server failed to start for {mode}/{thinking}", flush=True)
            return 2

        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        runner_cmd = [
            sys.executable, "-m", "plaincivic.runner",
            "--base-url", base_url,
            "--mode", mode,
            "--thinking", thinking,
        ]
        if cases_arg:
            runner_cmd.extend(["--cases", cases_arg])
        if resume:
            runner_cmd.append("--resume")

        return subprocess.run(runner_cmd, cwd=str(ROOT), env=env, check=False).returncode
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        log_f.close()
        time.sleep(1.5)


def main() -> int:
    server_exe = find_llama_server()
    if not server_exe or not GGUF_PATH.exists():
        print("[ERROR] Missing llama-server.exe or Spark-X2.6-4B-Q4_K_M.gguf")
        return 1

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="", help="Comma-separated case IDs")
    parser.add_argument("--only", default="", help="Comma-separated run names e.g. skill_v2_low,skill_v2_none")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    cases_arg = args.cases
    resume = not args.no_resume
    only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    plan = [
        ("baseline_v1", "low", 512, 8084),
        ("skill_v2", "none", 0, 8085),
        ("skill_v2", "low", 512, 8086),
        ("skill_v2", "high", 1400, 8087),
    ]

    for mode, thinking, budget, port in plan:
        rname = f"{mode}_{thinking}"
        if only_set and rname not in only_set:
            continue
        rc = run_with_server(server_exe, GGUF_PATH, mode, thinking, budget, port, cases_arg=cases_arg, resume=resume)
        if rc != 0:
            print(f"[WARN] {rname} returned {rc}", flush=True)

    # Render interactive HTML demo using best skill_v2 run (skill_v2_high or skill_v2_low)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    best_run = "skill_v2_high"
    # Pick highest accuracy run automatically if summaries exist
    scores = []
    for cand in ("skill_v2_high", "skill_v2_low", "skill_v2_none"):
        sp = ROOT / "runs" / cand / "summary.json"
        if sp.exists():
            sd = json.loads(sp.read_text(encoding="utf-8"))
            scores.append(((sd.get("overall_accuracy", 0), sd.get("trap_pass_rate", 0), sd.get("clause_survival_rate", 0)), cand))
    if scores:
        scores.sort(reverse=True)
        best_run = scores[0][1]
    print(f"\n[DEMO] Rendering demo/index.html from best run: {best_run}", flush=True)
    subprocess.run([sys.executable, "-m", "plaincivic.render_demo", best_run], cwd=str(ROOT), env=env, check=True)
    print("[ALL DONE]", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
