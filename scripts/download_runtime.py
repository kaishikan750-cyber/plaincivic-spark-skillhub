"""Download official llama.cpp b12671 CUDA runtime and Spark-X2.6-4B-Q4_K_M.gguf to D:\\spark-runtime."""

import hashlib
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

RUNTIME_ROOT = Path(r"D:\tools\spark-runtime")
LLAMA_DIR = RUNTIME_ROOT / "llama-b12671-cuda12.4"
MODEL_DIR = RUNTIME_ROOT / "models" / "XHToken--Spark-X2.6-4B-GGUF"

LLAMA_ZIPS = [
    (
        "llama-b12671-bin-win-cuda-12.4-x64.zip",
        "https://github.com/ggml-org/llama.cpp/releases/download/b12671/llama-b12671-bin-win-cuda-12.4-x64.zip",
    ),
    (
        "cudart-llama-bin-win-cuda-12.4-x64.zip",
        "https://github.com/ggml-org/llama.cpp/releases/download/b12671/cudart-llama-bin-win-cuda-12.4-x64.zip",
    ),
]

GGUF_FILE = "Spark-X2.6-4B-Q4_K_M.gguf"
GGUF_REVISION = "9d716770ac7477776de5f891f70cdf98b003a5cd"
GGUF_URLS = [
    f"https://huggingface.co/XHToken/Spark-X2.6-4B-GGUF/resolve/{GGUF_REVISION}/{GGUF_FILE}",
    f"https://hf-mirror.com/XHToken/Spark-X2.6-4B-GGUF/resolve/{GGUF_REVISION}/{GGUF_FILE}",
]


def download_with_resume(url: str, dest: Path, label: str) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    existing = part.stat().st_size if part.exists() else 0

    headers = {"User-Agent": "PlainCivic-Runtime-Setup/1.0"}
    if existing > 0:
        headers["Range"] = f"bytes={existing}-"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = getattr(resp, "status", 200)
            content_len = int(resp.headers.get("Content-Length", 0))
            if status == 206:
                total = existing + content_len
                mode = "ab"
            else:
                total = content_len
                existing = 0
                mode = "wb"

            print(f"[{label}] Downloading {url} -> {dest} ({total / 1024 / 1024:.1f} MB, resume={existing / 1024 / 1024:.1f} MB)", flush=True)
            t0 = time.time()
            downloaded = existing
            last_log = t0
            with open(part, mode) as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_log >= 5.0:
                        elapsed = max(now - t0, 0.01)
                        speed = (downloaded - existing) / 1024 / 1024 / elapsed
                        pct = (downloaded / total * 100) if total else 0
                        print(f"  [{label}] {downloaded / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} MB ({pct:.1f}%) @ {speed:.2f} MB/s", flush=True)
                        last_log = now

            if total > 0 and downloaded < total:
                print(f"[{label}] Incomplete download ({downloaded} < {total})", flush=True)
                return False

        part.replace(dest)
        print(f"[{label}] DONE: {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)", flush=True)
        return True
    except Exception as exc:
        print(f"[{label}] Failed from {url}: {exc}", flush=True)
        return False


def main() -> int:
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    LLAMA_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download & extract llama.cpp CUDA 12.4 zips
    for fname, url in LLAMA_ZIPS:
        zdest = RUNTIME_ROOT / fname
        if not zdest.exists():
            ok = download_with_resume(url, zdest, fname)
            if not ok:
                return 1
        else:
            print(f"[{fname}] Cached: {zdest}", flush=True)

        marker = LLAMA_DIR / f".extracted_{fname}"
        if not marker.exists():
            print(f"[{fname}] Extracting to {LLAMA_DIR}...", flush=True)
            with zipfile.ZipFile(zdest, "r") as zf:
                zf.extractall(LLAMA_DIR)
            marker.write_text("ok", encoding="utf-8")

    # 2. Download Spark-X2.6-4B-Q4_K_M.gguf
    gguf_dest = MODEL_DIR / GGUF_FILE
    if gguf_dest.exists() and gguf_dest.stat().st_size > 3_000_000_000:
        print(f"[GGUF] Reusing cached weights: {gguf_dest} ({gguf_dest.stat().st_size / 1024 / 1024:.1f} MB)", flush=True)
    else:
        ok = False
        for url in GGUF_URLS:
            if download_with_resume(url, gguf_dest, GGUF_FILE):
                ok = True
                break
        if not ok:
            print("[GGUF] All download URLs failed!", flush=True)
            return 2

    # Verify llama-server.exe exists
    server_exe = next(LLAMA_DIR.rglob("llama-server.exe"), None)
    print(f"[VERIFY] llama-server.exe = {server_exe}", flush=True)
    print(f"[VERIFY] gguf_dest = {gguf_dest} ({gguf_dest.stat().st_size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
