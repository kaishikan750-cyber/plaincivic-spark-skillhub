# PlainCivic · 办事明鉴

> **HER Hack-Astron #8 (`Spark × SkillHub` Agent Skills Challenge)** — Track: **Accessibility and languages (无障碍与多语言)**
>
> Simplify public-service guides and generate bilingual (ZH/EN) + WCAG-AAA plain-language step-by-step readiness checklists on-device, verifying that **eligibility**, **required documents**, and **deadlines** survive the rewrite with zero hallucination.

## Why PlainCivic?

Official Chinese public-service guides (immigration residence permits, visa extensions, passport renewal, cross-province medical insurance, residence permits, community subsidies) are dense bureaucratic documents packed with conditional clauses, original-vs-copy rules, validity windows, and hard advance deadlines.

- **Non-Chinese-speaking residents** and **elderly / visually impaired / first-time applicants** frequently suffer wasted counter trips (**“白跑一趟”**) or missed legal deadlines when generic chatbots simplify or translate notices and silently drop copy counts, advance windows, or conditional triggers.
- **Privacy by design**: Applicant profiles and personal document inventories stay 100% on-device — local **`Spark-X2.6-4B`** runs entirely on the user's laptop GPU via `llama.cpp` with zero cloud upload of personal documents.

## Architecture: Clear 3-Layer Division of Labor

1. **SkillHub Skill (`global/生活办事材料核验管家`, v`20260716.135124`)**
   - Retrieved directly from the official SkillHub registry (`https://skill.xfyun.cn`) with full SHA-256 provenance recorded in `skills/PROVENANCE.json`.
   - Governs the 6-step read-only protocol: Source Registry → Blind Extraction (before viewing user inventory) → Conditional Resolution without guessing identity (`unknown` → `needs_confirmation`) → Reference-Date Arithmetic & Inventory Matching → Deterministic Overall Status → Quality Gate via the skill's own `scripts/validate_readiness.py --strict`.
2. **Local `Spark-X2.6-4B` (`XHToken/Spark-X2.6-4B-GGUF`, `Q4_K_M`, rev `9d716770ac7477776de5f891f70cdf98b003a5cd`)**
   - Runs locally on RTX 4060 Laptop GPU via `llama.cpp b12671` (Vulkan).
   - Performs blind requirement extraction (Stage A), conditional reasoning & reference-date math, inventory matching, and accessible plain-language ZH + bilingual EN step generation (Stage B).
   - Benchmarked across all 3 official controllable thinking budgets: `enable_thinking=False` (`none`), `reasoning_effort="low"`, and `reasoning_effort="high"`.
3. **Deterministic Verification & Accessible Demo Viewer (`src/plaincivic/`)**
   - `verifier.py` enforces verbatim source-quote grounding, unreadable-section gating, and calls official `skills/life-service-doc-verifier/scripts/validate_readiness.py --strict` on every run.
   - `render_demo.py` renders an offline interactive HTML viewer (`demo/index.html`) supporting Standard View, **Elderly Large-Font High-Contrast Mode (WCAG AAA)**, **Bilingual Side-by-Side ZH/EN**, **Screen-Reader Linearized Text**, click-to-highlight verbatim quotes, and full thinking-budget benchmark dashboards.

## Pre-Inference Gold Commitment

All 10 benchmark cases (`cases/C01`–`C10`), gold labels (`gold/gold.json`), acceptance protocol (`gold/ACCEPTANCE.md`), and SkillHub provenance (`skills/PROVENANCE.json`) were committed to Git (`61d9137`) **before downloading weights or running the first local inference**.

## Quick Reproduction

```powershell
# 1. Run deterministic verifier & official SkillHub --strict unit tests
python tests/test_verifier.py

# 2. Place official llama.cpp b12671+ and Spark-X2.6-4B-Q4_K_M.gguf under D:\tools\spark-runtime\
#    (SHA-256: 91cb2811aebb47ac916aa619d27d4cdd7f4143106b7917accb8ead4cd7f5cbd9)

# 3. Run all 4 ablation configs (Baseline v1 + PlainCivic v2 none/low/high) and build demo/index.html
python scripts/run_all_benchmarks.py

# 4. Capture consecutive walkthrough screenshots and thinking-budget charts
python scripts/capture_demo_screenshots.py
```

## Results (`n = 10` Pre-Committed Cases, 40 Full Local RTX 4060 GPU Runs)

| Configuration (Local `Spark-X2.6-4B-Q4_K_M`) | Overall Verdict Accuracy | Edge-Case Trap Pass | Clause Survival Rate | SkillHub `--strict` (Pre → Post) | Verbatim Quote Grounding | Avg Latency | Avg Tokens (Speed) |
|---|---|---|---|---|---|---|---|
| **Baseline v1** (`thinking=low`, single-pass) | 7/10 (70%) | 6/10 (60%) | 58/73 (79.5%) | 0/10 → **0/10** | 61.1% → 61.1% | 52.8s | 2,565 tok (48.6 tok/s) |
| **PlainCivic v2** (`SkillHub`, `thinking=none`, `budget=0`) | 7/10 (70%) | **10/10 (100%)** | 63/73 (86.3%) | 0/10 → **10/10** | **100.0% → 100.0%** | **44.4s** | **1,995 tok** (45.0 tok/s) |
| **PlainCivic v2** (`SkillHub`, `thinking=low`, `budget=512`) | **9/10 (90%)** | **10/10 (100%)** | 64/73 (87.7%) | 0/10 → **10/10** | **100.0% → 100.0%** | 79.0s | 3,625 tok (45.9 tok/s) |
| **PlainCivic v2** (`SkillHub`, `thinking=high`, `budget=1400`) | **9/10 (90%)** | **10/10 (100%)** | **68/73 (93.2%)** | 0/10 → **10/10** | **100.0% → 100.0%** | 121.6s | 5,547 tok (45.6 tok/s) |

Full ready-to-publish submission drafts live in [`submission/HF_DISCUSSION_POST.md`](submission/HF_DISCUSSION_POST.md) and [`submission/GITHUB_ISSUE_32_REPLY.md`](submission/GITHUB_ISSUE_32_REPLY.md).

## Limitations & Boundaries

- PlainCivic is strictly a **read-only** preparation and accessibility aid. It does not submit forms, book appointments, or provide legal/immigration advice.
- Policy rules vary by city and update frequently; users must always verify final eligibility and counter requirements against the local `.gov.cn` portal or counter staff.
