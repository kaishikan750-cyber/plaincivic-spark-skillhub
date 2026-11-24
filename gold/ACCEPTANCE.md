# PlainCivic Acceptance Protocol & Gold Evaluation Criteria

**Status:** Pre-committed BEFORE running local `Spark-X2.6-4B` inference.
**Track:** Accessibility and languages (无障碍与多语言) — *Simplify a public-service guide or produce bilingual instructions. Check that eligibility, required documents and deadlines survive the rewrite.*
**SkillHub Skill:** `global/生活办事材料核验管家` (version `20260716.135124`)

---

## 1. Pre-Committed Evaluation Dimensions

Every case in `cases/` (`C01`–`C10`) is evaluated against `gold/gold.json` using deterministic automated checks plus explicit human-review inspection:

1. **Overall Readiness Decision (`overall_status`)**
   - Exact match against gold (`ready`, `not_ready`, or `needs_confirmation`) computed strictly via SkillHub's algorithm:
     - Any applicable requirement is `missing`, `expired`, or `conflict` → `not_ready`
     - Otherwise, any requirement is `needs_confirmation` (including `unknown` condition or unreadable critical section) → `needs_confirmation`
     - Otherwise, all applicable requirements are `ready` → `ready`

2. **SkillHub Strict Quality Gate (`scripts/validate_readiness.py --strict`)**
   - The output `readiness.json` must pass the official SkillHub package's own validator with **0 errors and 0 warnings** (`valid: true`).

3. **Zero-Hallucination Source Grounding (Verbatim Quote Check)**
   - Every requirement's `evidence[].quote` must appear verbatim (after whitespace normalization) inside the registered source text referenced by `source_id`.
   - Zero invented mandatory documents: items not stated in the notice must NOT be promoted into `required` requirements.
   - Zero invented deadlines or fees: in Case `C08` (no deadline stated, free of charge), inventing a deadline or fee is counted as a hallucination failure.

4. **Clause Survival Rate Across Plain-Language & Bilingual Rewrite**
   - Each gold case defines a fixed list of critical **survival clauses** grouped into three categories:
     - **Eligibility (`eligibility`)**: age thresholds, residence duration (e.g., `半年` / `6 months`), validity thresholds (`不足六个月` / `1年以上`), etc.
     - **Required Documents (`documents`)**: exact format/copy/validity qualifiers (e.g., `原件` / `original`, `复印件2份` / `2 copies`, `白底` / `white background`, `30日内` / `within 30 days`).
     - **Deadlines & Timeframes (`deadlines`)**: hard calendar dates/times (`2026年11月30日17:00`), advance windows (`届满7日前` / `7 days before`), post-entry windows (`入境之日起30日内` / `within 30 days`), processing limits (`15个工作日` / `1个工作日`).
   - A clause **survives** if the generated plain-language checklist (and English bilingual translation for bilingual cases `C01`, `C02`, `C10`) preserves the exact quantitative/conditional constraint without dropping or distorting it.

5. **Critical Trap Handling (7 Named Edge-Case Traps)**
   - `T1_expiry_date_math`: Accurately compute expiration/window against `reference_date` (`2026-11-24`) (`C01`, `C02`, `C05`, `C09`).
   - `T2_format_original_vs_photo`: Catch phone-photo-instead-of-original (`C05`), wrong photo background (`C01`), or insufficient copy count (`C09`).
   - `T3_unknown_identity_no_guess`: When applicant profile omits a conditional trigger (`C04`), output `applicability: "unknown"` and `status: "needs_confirmation"` rather than guessing.
   - `T4_not_applicable_no_false_block`: Do NOT falsely fail an applicant for a conditional item that clearly does not apply (`C01` solo applicant, `C03` retired private employee / adult, `C06` unmarried applicant).
   - `T5_multi_source_conflict`: When two notices conflict (`C07`: `S1` vs `S2`), cite BOTH sources side-by-side and mark `conflict` without silently choosing one.
   - `T6_no_invented_deadline_or_fee`: When a notice has no deadline and is free (`C08`), do not invent a deadline or fee.
   - `T7_unreadable_section_gate`: When a critical annex/table is unreadable (`C10`), downgrade `overall_status` to at least `needs_confirmation` and refuse to invent unreadable figures.

---

## 2. Controlled Ablation Plan

1. **Method Comparison (all 10 cases, local `Spark-X2.6-4B-Q4_K_M`, `temperature=0.2`, fixed seed `42`):**
   - **Baseline v1**: Single-pass prompt asking local `Spark-X2.6-4B` directly to simplify/translate and judge readiness without SkillHub extraction-first separation or deterministic validation.
   - **PlainCivic v2 (Skill-Guided)**: Follows `生活办事材料核验管家` v`20260716.135124` two-stage protocol (Stage A: extract requirements & quotes from source notices BEFORE seeing user inventory → Stage B: condition resolution, date arithmetic & plain-language/bilingual synthesis → Stage C: deterministic quote check + clause survival audit + SkillHub `validate_readiness.py --strict` repair/downgrade gate).
2. **Spark-X2.6-4B Controllable Thinking Budget Comparison (all 10 cases under PlainCivic v2):**
   - `thinking=none` (`enable_thinking=false`)
   - `thinking=low` (`reasoning_effort="low"`)
   - `thinking=high` (`reasoning_effort="high"`)
   - Metrics recorded per case: wall-clock latency (s), completion tokens, tokens/sec, overall accuracy, clause survival rate, trap pass rate, and SkillHub `--strict` pass rate.

---

## 3. Privacy & Application Boundaries

- **Zero private personal data**: All public notices are derived from publicly published `.gov.cn` guidelines (with URLs and retrieval date `2026-11-24` recorded) or explicitly tagged synthetic civic edge cases (`synthetic_civic_notice`). All applicant profiles and document inventories are synthetic demonstration fixtures containing zero real ID numbers, addresses, or personal data.
- **Non-authoritative boundary**: PlainCivic is a read-only pre-trip preparation and accessibility aid. It does NOT submit applications, book appointments, provide legal/immigration counsel, or replace final verification by the official counter or local `.gov.cn` portal.
