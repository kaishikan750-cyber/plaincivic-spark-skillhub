Hi @FenjuFu and the HER Hack-Astron #8 reviewers! Submitting my individual entry for the **Accessibility and languages (无障碍与多语言)** track:

- **Project:** **PlainCivic · 办事明鉴** — On-device bilingual (ZH/EN) & WCAG-AAA plain-language public-service readiness checker
- **Full Entry (Hugging Face Community Discussion):** `<PASTE_YOUR_HF_DISCUSSION_URL_HERE>` *(e.g. `https://huggingface.co/XHToken/Spark-X2.6-4B/discussions/47`)*
- **SkillHub Skill Used:** `global/生活办事材料核验管家` (`v20260716.135124`, including its built-in `scripts/validate_readiness.py --strict` quality gate)
- **Local Model & Hardware:** `XHToken/Spark-X2.6-4B-GGUF` (`Q4_K_M`, rev `9d716770`, verified SHA-256) running locally on NVIDIA RTX 4060 Laptop GPU via `llama.cpp b12671` (Vulkan)
- **Key Verified Result (10 pre-committed cases, 40 local runs):** Compared to Baseline v1 (`7/10` verdict, `6/10` traps, `79.5%` clause survival, `0/10` SkillHub `--strict`), PlainCivic v2 (`high` thinking budget) reaches **`9/10` verdict accuracy, `10/10` (100%) edge-case trap pass, `93.2%` (68/73) clause survival, `100%` verbatim quote grounding, and `10/10` SkillHub `--strict` pass (0 errors, 0 warnings)**, with full thinking-budget ablation (`none` / `low` / `high`) and honest failure logs included.
- **Contributor:** `<YOUR_NAME_OR_HANDLE>` (`<YOUR_HF_OR_GITHUB_PROFILE_URL>`, individual entry)
