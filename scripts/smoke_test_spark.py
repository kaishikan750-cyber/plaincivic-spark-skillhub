"""Verify GGUF SHA-256, boot llama-server on RTX 4060 Vulkan GPU, and smoke-test none/low/high thinking modes."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\Users\qqq\.gemini\antigravity\scratch\plaincivic-spark-skillhub")
sys.path.insert(0, str(ROOT / "src"))

from plaincivic.spark_client import LocalSparkClient  # noqa: E402

SERVER_EXE = Path(r"D:\tools\spark-runtime\llama-b12671-vulkan\llama-server.exe")
GGUF_PATH = Path(r"D:\tools\spark-runtime\models\XHToken--Spark-X2.6-4B-GGUF\Spark-X2.6-4B-Q4_K_M.gguf")
EXPECTED_SHA = "91cb2811aebb47ac916aa619d27d4cdd7f4143106b7917accb8ead4cd7f5cbd9"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print("[1/3] Computing SHA-256 of Spark-X2.6-4B-Q4_K_M.gguf ...", flush=True)
    actual_sha = sha256_file(GGUF_PATH)
    print(f"  Actual SHA-256:   {actual_sha}", flush=True)
    print(f"  Expected SHA-256: {EXPECTED_SHA}", flush=True)
    print(f"  Exact match:      {actual_sha == EXPECTED_SHA}", flush=True)

    ver_out = subprocess.run([str(SERVER_EXE), "--version"], capture_output=True, text=True, check=False)
    print("[2/3] llama-server --version:", (ver_out.stdout + ver_out.stderr).strip(), flush=True)

    log_path = ROOT / "runs" / "smoke_server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(log_path, "w", encoding="utf-8")

    cmd = [
        str(SERVER_EXE),
        "-m", str(GGUF_PATH),
        "-ngl", "99",
        "-c", "16384",
        "--jinja",
        "--host", "127.0.0.1",
        "--port", "8081",
    ]
    print("[3/3] Starting llama-server:", " ".join(cmd), flush=True)
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
    client = LocalSparkClient(base_url="http://127.0.0.1:8081")
    try:
        healthy = False
        for _ in range(60):
            try:
                client.health()
                healthy = True
                break
            except Exception:
                time.sleep(1.0)
        if not healthy:
            print("ERROR: Server did not become healthy. Log tail:")
            log_f.close()
            print(log_path.read_text(encoding="utf-8", errors="ignore")[-2000:])
            return 1

        print("Server HEALTHY! Testing none / low / high thinking budgets...", flush=True)
        msgs = [
            {"role": "user", "content": "如果入境日期是2026-11-01，政策要求入境30日内办理居留许可，截止日期是哪天？请简短回答。"}
        ]
        for mode in ("none", "low", "high"):
            r = client.chat(msgs, thinking_mode=mode, temperature=0.2, max_tokens=512, seed=42)
            print(
                f"  mode={mode:4s} | wall={r.wall_seconds:.2f}s | tok={r.completion_tokens} "
                f"| speed={r.tokens_per_sec} tok/s | think_len={len(r.reasoning_content)} | ans={r.content[:100]!r}",
                flush=True,
            )
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
