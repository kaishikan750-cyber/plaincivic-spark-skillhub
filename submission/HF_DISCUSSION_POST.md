# [HER Hack-Astron #8] [Spark × SkillHub] PlainCivic · 办事明鉴 — Bilingual & Accessible Public-Service Readiness Checker (On-Device)

> **Track:** Accessibility and languages (无障碍与多语言)
> **SkillHub Skill:** [`global/生活办事材料核验管家`](https://skill.xfyun.cn/space/global/%E7%94%9F%E6%B4%BB%E5%8A%9E%E4%BA%8B%E6%9D%90%E6%96%99%E6%A0%B8%E9%AA%8C%E7%AE%A1%E5%AE%B6) (`v20260716.135124`)
> **Local Model:** [`XHToken/Spark-X2.6-4B-GGUF`](https://huggingface.co/XHToken/Spark-X2.6-4B-GGUF) (`Spark-X2.6-4B-Q4_K_M.gguf`, rev `9d716770ac7477776de5f891f70cdf98b003a5cd`, SHA-256 `91cb2811...5cbd9`) running 100% locally on an NVIDIA RTX 4060 Laptop GPU via `llama.cpp b12671` (Vulkan).
> **Repository (code, pre-committed gold labels, raw Spark traces, interactive WCAG-AAA demo & screenshots):** `<REPLACE_WITH_YOUR_GITHUB_REPO_URL>`

---

## Project and track

- **Project name:** PlainCivic · 办事明鉴 — Bilingual & Plain-Language Public-Service Readiness Checker
- **Track:** **Accessibility and languages (无障碍与多语言)** — *Simplify a public-service guide or produce bilingual instructions. Check that eligibility, required documents and deadlines survive the rewrite.*

---

## User and task

### Who uses the result, and what problem do they face?

Two underserved real-world groups frequently suffer wasted counter trips (**“白跑一趟”**) or missed statutory windows when preparing for Chinese public-service errands (immigration work residence permits, visa extensions, passport renewal, cross-province medical insurance filing, city residence permits, accessible library cards, community youth programs, and graduate subsidies):

1. **Non-Chinese-speaking residents & international graduates in China** who face dense bureaucratic Chinese `.gov.cn` guidelines containing hidden conditional triggers (`申请有效期1年以上…`), photo/original traps (`近期白底彩色免冠照片`, `原件及复印件2份`), and legal deadlines (`入境之日起30日内`, `停留期限届满7日前`, `2026年11月30日17:00`).
2. **Elderly, visually impaired, and first-time citizen applicants** (and family members acting as proxies) who struggle with wall-of-text notices and need large-font high-contrast (WCAG AAA) or screen-reader-linearized step-by-step checklists matched against what documents they actually hold in hand.

**Why on-device execution matters:** Personal document inventories (passport expiry, entry date, health check dates, marital/disability status, housing contracts) are deeply private. Running `Spark-X2.6-4B` locally guarantees that sensitive applicant details never leave the user's laptop.

### Sample input and acceptance criteria chosen before the run

- **Pre-inference lock:** All 10 cases (`cases/C01`–`C10`), acceptance rules (`gold/ACCEPTANCE.md`), gold labels (`gold/gold.json`), and SkillHub package provenance (`skills/PROVENANCE.json`) were committed to Git (**commit `61d9137`**) **before downloading weights or executing the first inference**.
- **Dataset (`n = 10`):**
  - 5 cases grounded in public `.gov.cn` guidance excerpts (`C01` NIA Work Residence Permit [bilingual], `C02` NIA L-Visa Extension [bilingual], `C03` Elderly Passport Renewal [ready], `C04` Cross-Province Medical Filing [`unknown` identity trap], `C05` City Residence Permit [6-month eligibility + phone-photo-vs-original trap]);
  - 5 explicitly tagged synthetic civic edge cases (`C06` Housing Fund Rent Withdrawal [unmarried exclusion, ready], `C07` Senior Free Transit Card [conflicting 2024 vs 2026 notices `S1` vs `S2`], `C08` Accessible Braille/Audio Library Card [no deadline stated & free of charge], `C09` Grandparent Proxy Youth Enrollment [54-day expired medical form + copy count mismatch + missing proxy letter], `C10` Graduate Rental Subsidy [bilingual hard deadline `2026-11-30 17:00` + illegible scanned Annex B]).
- **Pre-committed acceptance criteria:**
  1. Exact `overall_status` match (`ready` / `not_ready` / `needs_confirmation`) computed per SkillHub's rule;
  2. Official SkillHub `scripts/validate_readiness.py --strict` passes with **0 errors and 0 warnings**;
  3. Verbatim source quote grounding (every `quote` appears verbatim in the registered source line);
  4. **Clause Survival Rate** across 73 pre-committed eligibility, document-format, deadline, and English bilingual clauses;
  5. All 7 named edge-case traps (`T1` date math, `T2` original/copy/photo format, `T3` no guessing `unknown` identity, `T4` `not_applicable` exclusion, `T5` side-by-side multi-source conflict, `T6` zero invented deadline/fee, `T7` unreadable-section gate).

---

## SkillHub skill and Spark-X2.6-4B

- **Skill name, detail page, source and version:**
  - Skill: `生活办事材料核验管家` (`global/生活办事材料核验管家`)
  - Detail page: `https://skill.xfyun.cn/space/global/%E7%94%9F%E6%B4%BB%E5%8A%9E%E4%BA%8B%E6%9D%90%E6%96%99%E6%A0%B8%E9%AA%8C%E7%AE%A1%E5%AE%B6`
  - Source: Official SkillHub public registry (`https://skill.xfyun.cn/api/v1/skills/global/.../versions/20260716.135124/download`)
  - Version: `20260716.135124` (ZIP SHA-256: `5ae081adc8973c051b740c2c9e2554c8c7807f964be9e9c509731f786c5db694`, `moderation.verdict: clean`; all 4 original files retained intact in `skills/life-service-doc-verifier/`, including `SKILL.md`, `agents/openai.yaml`, `references/output-contracts.md`, and `scripts/validate_readiness.py`).
- **Agent host and steps guided by the skill:**
  - Host: Antigravity local Python orchestrator (`src/plaincivic/`) following all 6 steps of `SKILL.md`:
    1. **Source registry & currentness tagging** (`S1..Sn`, `user_provided_current`);
    2. **Stage A — Blind extraction** (extracts formal requirements, verbatim quotes, conflicts, and unreadable sections *before* exposing user inventory, obeying Rule #1);
    3. **Stage B — Condition resolution (`applies`/`not_applicable`/`unknown`), reference-date arithmetic, inventory matching, and accessible ZH / bilingual EN rewrite** (obeying Rules #2–#5);
    4. **Stage C — Deterministic contract gate & official SkillHub quality gate** (`verifier.py` hydrates exact verbatim lines, preserves multi-source conflicts, enforces the unreadable-section gate, and invokes the skill's own `python skills/life-service-doc-verifier/scripts/validate_readiness.py readiness.json --strict`).
- **Model source, revision and step performed by Spark:**
  - Model: `XHToken/Spark-X2.6-4B-GGUF` (`Spark-X2.6-4B-Q4_K_M.gguf`, 3,543,441,312 bytes, HF revision `9d716770ac7477776de5f891f70cdf98b003a5cd`, fetched via identical official ModelScope mirror `XHToken/Spark-X2.6-4B-GGUF` rev `8500d75a`, verified byte-for-byte SHA-256 `91cb2811aebb47ac916aa619d27d4cdd7f4143106b7917accb8ead4cd7f5cbd9`).
  - Steps performed locally by `Spark-X2.6-4B`: Stage A blind structured requirement/quote/conflict/unreadable extraction + Stage B conditional applicability reasoning, reference-date calculation, inventory mismatch detection, and plain-language ZH + bilingual EN step generation.
- **Other models, tools or services and their roles:**
  - `llama.cpp` `b12671` (Vulkan GPU server on RTX 4060): local OpenAI-compatible inference engine with native `spark2_5` support and `--reasoning-budget` / `--reasoning-effort` controls;
  - Deterministic Python scripts (`verifier.py`, official `validate_readiness.py --strict`, `render_demo.py`): zero-LLM verification, survival auditing, and WCAG-AAA HTML rendering. No external LLM APIs were called during evaluation.

---

## Demo (Illustrated Walkthrough)

> *(Upload the 7 PNG files from `demo/screenshots/` into this Hugging Face Discussion post or link them from your GitHub repo!)*

### Walkthrough Screenshots with Captions

1. **Hero Case `C01` — Bilingual ZH/EN Side-by-Side + Click-to-Highlight Verbatim Source Evidence (`S1:L6`)**
   ![01_c01_bilingual_evidence_highlight](demo/screenshots/01_c01_bilingual_evidence_highlight.png)
   *Caption: Local `Spark-X2.6-4B` (`high`) inspects the NIA 2-year work residence permit guide (`S1`) and applicant inventory (`I01`–`I05`), issues a `not_ready` verdict (`DO NOT GO YET`), catches the blue-background photo (`I03`) and 8-month-expired foreign clinic copy (`I05`), excludes accompanying family proof (`not_applicable`), preserves key clauses in both Chinese plain language and English, and passes SkillHub `validate_readiness.py --strict` (0 errors, 0 warnings).*

2. **Hero Case `C01` — Verifiable Execution Trace (`Spark-X2.6-4B` `<think>` + Raw JSON + Stage C Gate)**
   ![02_c01_spark_raw_trace_and_gate](demo/screenshots/02_c01_spark_raw_trace_and_gate.png)
   *Caption: Full audit trace panel showing exact Stage A blind extraction (3,693 tok @ 45.7 tok/s), Stage B `<think>` reasoning + structured JSON (5,053 tok @ 44.2 tok/s), 100% verbatim quote grounding (9/9), and Stage C contract audit.*

3. **Accessibility Showcase `C04` — Elderly Large-Font High-Contrast Mode (WCAG AAA) + No-Identity-Guessing Rule**
   ![03_c04_elderly_wcag_aaa_unknown_trap](demo/screenshots/03_c04_elderly_wcag_aaa_unknown_trap.png)
   *Caption: 71-year-old retiree cross-province medical filing (`C04`) rendered in WCAG AAA dark-gold large-font mode (`21px+`). Because the profile omits whether the retiree holds a local residence permit or hospital referral, Spark obeys SkillHub Rule #2 (`applicability="unknown"` → `needs_confirmation`) instead of guessing.*

4. **Multi-Source Conflict `C07` — Side-by-Side Conflicting Civic Notices (`S1` 2024 vs `S2` 2026)**
   ![04_c07_multi_source_conflict](demo/screenshots/04_c07_multi_source_conflict.png)
   *Caption: Unlike Baseline v1 (which silently picked `S2` and falsely told the 62-year-old applicant `ready`), PlainCivic v2 cites BOTH `S1:L2` (age ≥ 65) and `S2:L2` (age ≥ 60) side-by-side with `status="conflict"` and blocks premature travel (`not_ready`).*

5. **Screen-Reader Accessibility `C08` — Linearized Plain-Text Mode + Zero-Hallucination No-Deadline Check**
   ![05_c08_screen_reader_linearized](demo/screenshots/05_c08_screen_reader_linearized.png)
   *Caption: Accessible Braille & Audio Library Card (`C08`) in linearized screen-reader plain text — accurately reports `ready`, zero fee, open Tue–Sun 09:00–17:00, and explicitly preserves "no application deadline" (`不设报名截止日期`) without inventing dates.*

6. **10-Case Ablation Table & Spark-X2.6-4B Thinking Budget Benchmark (`none` / `low` / `high`)**
   ![06_benchmark_table_10_cases](demo/screenshots/06_benchmark_table_10_cases.png)
   ![07_thinking_budget_chart](demo/screenshots/07_thinking_budget_chart.png)

### Actual Input → Raw Spark Output → Final Artifact → Human Review (`C01`)

- **Actual Input (`C01`, ref date `2026-11-24`):** 9-line NIA work residence permit guide (`S1:L1`–`L9`) + 5 synthetic applicant inventory items (`I01` passport entered `2026-11-01`, `I02` signed form, `I03` **blue-background** photos, `I04` stamped work permit, `I05` **2026-03-10 overseas clinic English copy**, >8 months old).
- **Raw Local `Spark-X2.6-4B` (`high`) Output (`runs/skill_v2_high/C01/trace.json`):**
  - *Stage A (blind to inventory, 80.9s, 45.7 tok/s):* Extracted all formal requirements (`L2`–`L9`), marking `L6` (`申请有效期1年以上`) and `L7` (`有随迁家属一同申请`) as `conditional`, with **100% verbatim quotes**.
  - *Stage B (114.4s, 44.2 tok/s):* Output `overall_status: "not_ready"`, marked photo (`I03`) `conflict`, medical certificate (`I05`) `expired`/`conflict` (>6 months & non-local copy), accompanying family (`L7`) `not_applicable`, and produced 5 aligned ZH + EN steps preserving `within 30 days`, `white-background`, `within 6 months`, `in person`, and `15 working days`.
- **Final Artifact:** Validated `runs/skill_v2_high/C01/readiness.json` (`validate_readiness.py --strict` → `{"valid": true, "errors": [], "warnings": []}`) + 6-section `readiness-report.md` + WCAG-AAA bilingual viewer `demo/index.html`.
- **Human Review Checkpoint:** Human reviewer inspects the 2 blocking actions (retake white-background photo; book local designated quarantine clinic medical exam before the `2026-12-01` 30-day post-entry deadline) and confirms city-specific appointment booking rules on the local PSB portal.

---

## Reproduction

### Installation and run steps

```powershell
# 1. Verify deterministic verifier & official SkillHub --strict validator (no GPU required)
python tests/test_verifier.py

# 2. Place llama.cpp b12671+ (Vulkan/CUDA) and Spark-X2.6-4B-Q4_K_M.gguf in D:\tools\spark-runtime\
#    Verify exact model SHA-256: 91cb2811aebb47ac916aa619d27d4cdd7f4143106b7917accb8ead4cd7f5cbd9
python scripts/smoke_test_spark.py

# 3. Run all 4 ablation configs (Baseline v1 + PlainCivic v2 none/low/high) across C01-C10 and build demo/index.html
python scripts/run_all_benchmarks.py

# 4. Regenerate consecutive walkthrough screenshots and thinking-budget charts
python scripts/capture_demo_screenshots.py
```

### Hardware, runtime version, precision/quantization, prompts and settings

- **Hardware:** Windows 11, Intel Core i5-13500HX (20 threads), 15.73 GB RAM, **NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM)**
- **Runtime:** `llama.cpp` `b12671` (`version: 1.0.0-dev, build 12671, commit ab789a246`, Windows x64 Vulkan), flags: `-ngl 99 -c 16384 --jinja`
- **Model & Quantization:** `XHToken/Spark-X2.6-4B-GGUF` → `Spark-X2.6-4B-Q4_K_M.gguf` (4-bit K-quant, 3.30 GiB, 100% offloaded to GPU)
- **Sampling & Thinking Budgets:** `seed=42`, `top_p=0.95`, `repeat_penalty=1.08`; `thinking=none` uses `temperature=0.2, --reasoning off, --reasoning-budget 0`; `thinking=low` uses `temperature=0.7, presence_penalty=0.4, --reasoning on --reasoning-effort low --reasoning-budget 512`; `thinking=high` uses `temperature=0.7, presence_penalty=0.4, --reasoning on --reasoning-effort high --reasoning-budget 1400`.
- **Prompts:** Full verbatim system/user prompts are version-controlled in `src/plaincivic/prompts.py` and logged verbatim in every `runs/<run>/<case>/trace.json`.

---

## Results and limitations

### Observed results, evaluation method and sample size (`n = 10` pre-committed cases, 40 full local GPU runs)

| Run Configuration | Overall Verdict Accuracy | Edge-Case Trap Pass Rate | Clause Survival Rate (73 clauses) | Official SkillHub `--strict` (Pre → Post) | Verbatim Quote Grounding (Pre → Post) | Avg Latency | Avg Tokens (Speed) |
|---|---|---|---|---|---|---|---|
| **Baseline v1** (`thinking=low`, single-pass) | 7/10 (70%) | 6/10 (60%) | 58/73 (79.5%) | 0/10 → **0/10** | 61.1% → **61.1%** | 52.8s | 2,565 tok (48.6 tok/s) |
| **PlainCivic v2** (`SkillHub`, `thinking=none`, `budget=0`) | 7/10 (70%) | **10/10 (100%)** | 63/73 (86.3%) | 0/10 → **10/10** | **100.0% → 100.0%** | **44.4s** | **1,995 tok** (45.0 tok/s) |
| **PlainCivic v2** (`SkillHub`, `thinking=low`, `budget=512`) | **9/10 (90%)** | **10/10 (100%)** | 64/73 (87.7%) | 0/10 → **10/10** | **100.0% → 100.0%** | 79.0s | 3,625 tok (45.9 tok/s) |
| **PlainCivic v2** (`SkillHub`, `thinking=high`, `budget=1400`) | **9/10 (90%)** | **10/10 (100%)** | **68/73 (93.2%)** | 0/10 → **10/10** | **100.0% → 100.0%** | 121.6s | 5,547 tok (45.6 tok/s) |

### Failures, improvements and points requiring human review (Honest Engineering Log)

1. **Failure #1 discovered & fixed (Low-temp CoT repetition loop + character counting spiral):** Initial experiments with `temperature=0.2` under thinking mode triggered a `<think>` repetition loop, and adding character-length hints (`8-28字`) caused `Spark-X2.6-4B` to burn 3,500+ tokens counting Chinese characters one by one. Removing character-count hints, aligning with the model card's higher sampling temperature (`0.7` + `presence_penalty=0.4`), and using `llama-server b12671`'s `--reasoning-budget` resolved truncation across all 40 runs.
2. **Failure #2 discovered & fixed (Stage C conflict-vs-unknown precedence):** Initially our Stage C gate overwrote `status="conflict"` to `needs_confirmation` whenever Spark labeled a multi-source conflict `applicability="unknown"` (`C07`). Preserving explicit `conflict` by aligning `applicability="applies"` lifted `skill_v2_none` traps from `9/10 → 10/10` and `skill_v2_low`/`high` `C07` verdicts to exact `not_ready`.
3. **Failure #3 observed across thinking budgets (`none` & `low` date arithmetic vs `high`):**
   - Under `thinking=none`, Spark made date/comparison errors (`23天已超30日` in an early test; misreading `I02` in `C04`).
   - Under `thinking=low` (`budget=512`), Spark made a real calendar slip on `C10` (claiming `2026-11-25` was past the `2026-11-30 17:00` deadline) and hit a budget cutoff (`已截断`) on `C05` before our JSON fallback guard recovered it.
   - Switching to `thinking=high` (`budget=1400`) fixed `C10` calendar reasoning and raised clause survival from `87.7%` to **`93.2% (68/73)`**.
4. **Residual failures still present in `skill_v2_high` (NOT hidden or gamed):**
   - **`C03` conservative downgrade (`needs_confirmation` vs gold `ready`):** Spark correctly reasoned `ready` for all 3 documents and `not_applicable` for both conditional traps, but emitted eligibility rule `R1` (`换发资格条件`) with `matched_inventory_ids: []` and wrote `现持护照` instead of referencing `I01`. Stage C conservatively downgraded `R1` to `needs_confirmation` to keep `validate_readiness.py --strict` at 0 errors.
   - **5/73 missed survival clauses (`C01` & `C10` EN `"1 year"`, `C07` `"2024"/"2026"` years in steps, `C08` exact wording `"免收押金与工本费"`):** E.g., in `C01` English steps Spark wrote `"for the 2-year residence application"` (correct for this user) instead of repeating the underlying general threshold `"over 1 year"`.
   - **Mandatory Human Review Boundaries:** Public-service policies change by district and municipality; counter staff hold final acceptance authority. PlainCivic is strictly read-only and must never replace official immigration, legal, or medical-insurance confirmation.

---

## Contributors and disclosure

- **Individual contributor:** `<REPLACE_WITH_YOUR_NAME_AND_HF_OR_GITHUB_PROFILE_URL>` (task selection, hardware confirmation, model retrieval, review of outputs and demo, final publication).
- **How AI assisted development:** Built with assistance from Antigravity (Gemini), which drafted the dataset scaffolding, Python orchestration/verifier code (`src/plaincivic/`), WCAG-AAA HTML demo template, and documentation; all 40 benchmark inferences were genuinely executed locally on the contributor's RTX 4060 GPU using `XHToken/Spark-X2.6-4B-GGUF` (`Q4_K_M`) and verified deterministically against the official SkillHub `validate_readiness.py --strict` script.
- **Data and dependency sources and permissions:**
  - SkillHub skill `global/生活办事材料核验管家` (`v20260716.135124`) from `https://skill.xfyun.cn`;
  - Model `XHToken/Spark-X2.6-4B-GGUF` (Apache 2.0 License);
  - Runtime `ggml-org/llama.cpp` `b12671` (MIT License);
  - `C01`–`C05` are condensed public-service guideline excerpts derived from public `.gov.cn` portals (`nia.gov.cn`, `gz.gov.cn`, `mps.gov.cn`, retrieved `2026-11-24`); `C06`–`C10` and all applicant inventories (`I01`–`I05`) are 100% synthetic demonstration fixtures containing zero real personal data or credentials.
