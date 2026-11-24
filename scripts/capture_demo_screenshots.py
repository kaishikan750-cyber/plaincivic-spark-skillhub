"""Capture consecutive high-resolution walkthrough screenshots and benchmark chart from real PlainCivic runs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEMO_HTML = ROOT / "demo" / "index.html"
SHOTS_DIR = ROOT / "demo" / "screenshots"
RUNS_DIR = ROOT / "runs"

CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]


def find_browser() -> Path:
    for p in CHROME_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError("No headless Chrome or Edge browser found")


def capture_shot(browser: Path, query: str, out_png: Path, width: int = 1440, height: int = 1080) -> None:
    url = DEMO_HTML.as_uri() + (f"?{query}" if query else "")
    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        "--virtual-time-budget=3000",
        f"--screenshot={out_png}",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not out_png.exists():
        raise RuntimeError(f"Screenshot failed for {out_png}: {proc.stderr}")
    print(f"[SHOT] {out_png.name} ({out_png.stat().st_size // 1024} KB) <- ?{query}")


def render_benchmark_chart(out_png: Path) -> None:
    order = ["baseline_v1_low", "skill_v2_none", "skill_v2_low", "skill_v2_high"]
    labels = ["Baseline v1\n(low)", "PlainCivic v2\n(think=none)", "PlainCivic v2\n(think=low)", "PlainCivic v2\n(think=high)"]
    summaries = []
    used_labels = []
    for key, lbl in zip(order, labels):
        sp = RUNS_DIR / key / "summary.json"
        if sp.exists():
            summaries.append(json.loads(sp.read_text(encoding="utf-8")))
            used_labels.append(lbl)
    if not summaries:
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4), dpi=160)
    x = list(range(len(summaries)))
    w = 0.25

    overall = [s["overall_accuracy"] * 100 for s in summaries]
    clauses = [s["clause_survival_rate"] * 100 for s in summaries]
    strict_post = [int(s["post_repair_strict_pass"].split("/")[0]) / s["cases"] * 100 for s in summaries]

    b1 = ax1.bar([i - w for i in x], overall, width=w, label="Overall Verdict Accuracy (%)", color="#2563eb")
    b2 = ax1.bar(x, clauses, width=w, label="Clause Survival Rate (%)", color="#16a34a")
    b3 = ax1.bar([i + w for i in x], strict_post, width=w, label="SkillHub --strict Pass (%)", color="#d97706")
    ax1.set_ylim(0, 128)
    ax1.set_xticks(x)
    ax1.set_xticklabels(used_labels, fontsize=9.5)
    ax1.set_ylabel("Percentage (%)")
    ax1.set_title("Quality Comparison Across 10 Pre-Committed Civic Cases")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    ax1.legend(loc="upper left", ncol=3, fontsize=7.8, frameon=True)
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 1.8, f"{h:.0f}%", ha="center", va="bottom", fontsize=8)

    lat = [s["avg_wall_seconds"] for s in summaries]
    toks = [s["avg_completion_tokens"] for s in summaries]
    bars_l = ax2.bar(x, lat, width=0.45, color="#0f766e", alpha=0.85, label="Avg Wall Latency (s / case)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(used_labels, fontsize=9.5)
    ax2.set_ylabel("Avg Latency per Case (seconds)", color="#0f766e")
    ax2.set_title("Spark-X2.6-4B Controllable Thinking Budget: Latency vs Tokens")
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, t in zip(bars_l, toks):
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + max(lat) * 0.03, f"{h:.1f}s\n({t:.0f} tok)", ha="center", va="bottom", fontsize=8.5)
    ax2.set_ylim(0, max(lat) * 1.28 if lat else 10)

    fig.suptitle("PlainCivic · Local Spark-X2.6-4B-Q4_K_M (RTX 4060 Vulkan) × SkillHub Benchmark", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    print(f"[CHART] {out_png.name} ({out_png.stat().st_size // 1024} KB)")


def main() -> int:
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    shots = [
        ("case=C01&view=bilingual&hl=S1:L6", SHOTS_DIR / "01_c01_bilingual_evidence_highlight.png", 1440, 1180),
        ("case=C01&view=std&openTrace=1", SHOTS_DIR / "02_c01_spark_raw_trace_and_gate.png", 1440, 1280),
        ("case=C04&view=elderly&hl=S1:L4", SHOTS_DIR / "03_c04_elderly_wcag_aaa_unknown_trap.png", 1440, 1180),
        ("case=C07&view=std&hl=S2:L2", SHOTS_DIR / "04_c07_multi_source_conflict.png", 1440, 1180),
        ("case=C08&view=sr", SHOTS_DIR / "05_c08_screen_reader_linearized.png", 1440, 960),
        ("view=bench", SHOTS_DIR / "06_benchmark_table_10_cases.png", 1440, 820),
    ]
    for q, out_p, w, h in shots:
        capture_shot(browser, q, out_p, w, h)
    render_benchmark_chart(SHOTS_DIR / "07_thinking_budget_chart.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
