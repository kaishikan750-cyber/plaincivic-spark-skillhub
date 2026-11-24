"""Prompt builders for Baseline v1 and SkillHub-guided PlainCivic v2 (`生活办事材料核验管家`)."""

from __future__ import annotations

import json
from typing import Any


def format_sources_block(sources: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for src in sources:
        header = (
            f"[{src['id']}] filename={src['filename']} | date={src['source_date']} "
            f"| type={src['source_type']} | currentness={src['currentness']}"
        )
        lines_str = "\n".join(src["lines"])
        blocks.append(f"{header}\n{lines_str}")
    return "\n\n".join(blocks)


def format_inventory_block(inventory: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {item['id']}: {item['name']}（{item['details']}）" for item in inventory
    )


def build_baseline_v1_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    """Baseline v1: naive single-pass prompt WITHOUT SkillHub extraction-first separation or strict contract."""
    bilingual_hint = (
        "同时提供英文双语版本（bilingual_steps_en）。"
        if case.get("mode") == "bilingual"
        else "无需英文翻译，bilingual_steps_en 留空数组 []。"
    )
    sys_msg = (
        "你是一个政务办事助手。请阅读办事通知和用户现有材料，帮用户简化办事指南并判断是否可以去办理。"
        "请只输出一个合法 JSON 对象，不要附加额外解释。"
    )
    user_msg = f"""参考日期：{case['reference_date']}
事项：{case['service']}
用户情况：{case['profile_summary']}

【办事通知原文】
{format_sources_block(case['sources'])}

【用户现有材料】
{format_inventory_block(case['inventory'])}

请输出 JSON，包含字段：
- overall_status: "ready" | "not_ready" | "needs_confirmation"
- summary_zh: 一句话结论
- requirements: 数组，每项含 id, item, necessity("required"|"conditional"|"optional"), condition(无则为null), applicability("applies"|"not_applicable"|"unknown"), status("ready"|"missing"|"expired"|"conflict"|"needs_confirmation"|"not_applicable"), matched_inventory_ids(数组), reason, evidence([{{source_id, locator, quote}}])
- actions: 数组，每项含 id, action, priority("blocking"|"high"|"normal"), evidence([{{source_id, locator, quote}}])
- plain_language_steps_zh: 通俗易懂的分步办事指南数组（保留资格条件、材料规格与截止时限）
- bilingual_steps_en: 英文对照步骤数组（{bilingual_hint}）
- questions: 待确认问题数组
- limitations: 局限说明数组
"""
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]


def build_stage_a_extraction_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    """SkillHub Stage A (Rule #1): Extract requirements strictly from source notices BEFORE seeing user inventory."""
    sys_msg = """你正在严格执行 SkillHub 技能「生活办事材料核验管家」(v20260716.135124) 的第 1 步【先提取要求，再查看现有材料】。
核心铁律（违反即判错）：
1. 你此刻看不到用户现有材料，只能依据下方通知原文逐条提取正式要求，严禁加入通知未写出的“常见材料”。
2. 每条要求必须附带来自原文的精确 source_id（如 "S1"）、locator（精确行号，如 "L4"）和 verbatim_quote（必须是从该行逐字复制的连续原文片段，严禁改写或拼凑）。
3. 清晰区分：
   - eligibility（办理条件/前置资格/年龄/居住时长/有效期门槛）
   - document（必备材料/条件材料，务必保留原件、复印件份数、照片底色、有效期天数等限定）
   - deadline（申请截止日期、提前天数、入境后天数、办理时限、受理窗口时间；若原文写明“不设报名截止日期”，必须原样保留，绝不捏造日期）
   - fee（收费或免收费条款）
4. 若同一事项存在多份来源（如 S1 和 S2）且要求互相冲突，必须在 conflicts 数组中并列写出双方 source_id、locator 和原文摘录，严禁自行裁定以哪份为准。
5. 若原文出现截断、模糊、扫描无法识别的附件/段落，必须记入 unreadable_sections，严禁猜测其中的数字或条件。
6. 仅输出一个严格合法的 JSON 对象，不要输出 Markdown 代码块之外的任何文字。"""

    user_msg = f"""事项名称：{case['service']}
参考日期：{case['reference_date']}

【登记来源全文】
{format_sources_block(case['sources'])}

请严格输出以下 JSON 结构：
{{
  "extracted_requirements": [
    {{
      "id": "R1",
      "category": "eligibility" | "document" | "deadline" | "fee" | "unreadable",
      "item": "原文材料、资格条件或时限要求名称",
      "necessity": "required" | "conditional" | "optional",
      "condition": "仅当 necessity 为 conditional 时填写完整触发条件；否则必须为 null",
      "constraints": "保留原文关键限定（如原件/复印件2份/白底/6个月内有效/入境30日内/届满7日前/15个工作日等）",
      "evidence": [
        {{"source_id": "S1", "locator": "L1", "quote": "必须逐字复制自对应行的连续子串"}}
      ]
    }}
  ],
  "multi_source_conflicts": [
    {{
      "topic": "冲突主题（如办理年龄/照片要求/费用）",
      "side_a": {{"source_id": "S1", "locator": "L2", "quote": "原文逐字摘录"}},
      "side_b": {{"source_id": "S2", "locator": "L2", "quote": "原文逐字摘录"}}
    }}
  ],
  "unreadable_sections": [
    {{"source_id": "S1", "locator": "L7", "quote": "原文不可读描述的逐字摘录"}}
  ],
  "key_deadlines_and_fees": [
    {{"label": "时限或费用说明", "exact_text": "原文精确表述", "source_id": "S1", "locator": "L2"}}
  ]
}}"""
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]


def build_stage_b_readiness_and_rewrite_messages(
    case: dict[str, Any],
    stage_a_json: dict[str, Any],
) -> list[dict[str, str]]:
    """SkillHub Stage B (Rules #2-#5): Condition resolution, date arithmetic, inventory matching, and plain-language/bilingual rewrite."""
    is_bilingual = case.get("mode") == "bilingual"
    bilingual_instruction = (
        """7. 【双语无障碍改写（Bilingual ZH/EN）】：
   - 必须同时输出 `plain_language_steps_zh`（中文大白话易读步骤，每步简短清晰、适合老人/读屏软件）和 `bilingual_steps_en`（精准英文对照步骤，面向外籍办事人）。
   - 所有关键资格门槛（如 1 year / 6 months / in person / 2 years）、材料硬限定（original / white background / 2 copies / health certificate within 6 months）和精确截止日期/时限（within 30 days / 7 days before expiry / 15 working days / 2026-11-30 17:00 / unreadable Annex B）必须在英文版与中文大白话版中 100% 存活，绝不允许被省略或模糊化！"""
        if is_bilingual
        else """7. 【中文无障碍易读改写（Plain-Language Accessible ZH）】：
   - 输出 `plain_language_steps_zh`（每步一句话讲清“干什么、带什么、何时办、哪里有坑”，适合长辈大字阅读与读屏软件线性朗读）。
   - 所有资格条件、原件/复印件份数、照片规格、有效期天数、免费/收费条款及截止时间（含“不设报名截止日期”）必须在改写中 100% 保留原文数值与限定，严禁为了通俗而删掉硬条件！
   - `bilingual_steps_en` 置为空数组 `[]`。"""
    )

    sys_msg = f"""你正在严格执行 SkillHub 技能「生活办事材料核验管家」(v20260716.135124) 的第 2–5 步【条件解析 → 对照现有材料 → 计算整体状态 → 生成可核验无障碍指南】。
严格契约规则（对应官方 scripts/validate_readiness.py --strict）：
1. 【不替用户猜身份】：每项要求的 `applicability` 只能是 `"applies"`、`"not_applicable"` 或 `"unknown"`。
   - 只有用户画像明确满足条件时才标 `"applies"`；
   - 明确排除时（如单身不适用“已婚”、退休民营企业员工不适用“登记备案国家工作人员”、单人申请不适用“随迁家属”、成年人不适用“未满16周岁”）必须标 `"applicability": "not_applicable"` 且 `"status": "not_applicable"`；
   - 用户画像未说明关键身份或选择时，**严禁猜测**，必须标 `"applicability": "unknown"` 且 `"status": "needs_confirmation"`！
2. 【契约约束】：
   - 若 `necessity == "conditional"`，`condition` 必须是非空字符串；若 `necessity` 为 `"required"` 或 `"optional"`，`condition` 必须为 `null`！
   - 若 `status == "ready"`，`matched_inventory_ids` 必须至少包含一个现有材料 ID（如 `["I01"]`）。
   - 若仅有手机照片而原文要求“原件”，或复印件份数不足，或照片底色不符，必须标 `"missing"` 或 `"conflict"`，绝不能标 `"ready"`！
   - 所有日期/期限必须以参考日期 `{case['reference_date']}` 为基准列出明确计算过程（例如 2026-03-10 至 2026-11-24 已超 8 个月 > 6 个月 → `expired`；2026-10-01 至 2026-11-24 已 54 天 > 30 日 → `expired`；2026-08-15 至 2026-11-24 仅约 3 个月 < 半年 → `conflict`；2026-11-29 距 2026-11-24 仅剩 5 天 < 提前 7 日 → `conflict` 或 `expired`）。
3. 【多源冲突】：若 Stage A 发现多份来源（S1 vs S2）冲突，必须在对应 requirement 中标 `"status": "conflict"`，并在 `evidence` 中同时保留 S1 与 S2 双方原文摘录，严禁擅自选一边！
4. 【不可读门禁】：若 Stage A 存在 `unreadable_sections`，必须为其建立一条 `status: "needs_confirmation"` 的 requirement（说明不可读部分并禁止编造内容），整体状态至少为 `needs_confirmation`！
5. 【整体状态算法（铁律）】：
   - 只要任一适用要求为 `"missing"`、`"expired"` 或 `"conflict"` → `overall_status` 必须为 `"not_ready"`；
   - 否则只要至少一项为 `"needs_confirmation"` → `overall_status` 必须为 `"needs_confirmation"`；
   - 否则全部适用项均为 `"ready"` → `overall_status` 必须为 `"ready"`。
6. 【原文证据保真】：所有 `evidence` 中的 `source_id`、`locator`、`quote` 必须直接沿用 Stage A 或原文逐字片段，绝不篡改。
{bilingual_instruction}
8. 仅输出一个严格合法的 JSON 对象，不要输出任何额外解释。"""

    user_msg = f"""【案件上下文】
- 事项名称：{case['service']}
- 参考日期：{case['reference_date']}
- 用户画像：{case['profile_summary']}
- 语言模式：{case['mode']}

【用户现有材料清单】
{format_inventory_block(case['inventory'])}

【Stage A 已从通知原文提取的要求（盲提结果）】
{json.dumps(stage_a_json, ensure_ascii=False, indent=2)}

【原始登记来源（仅供复核原文逐字引用）】
{format_sources_block(case['sources'])}

请严格输出符合 SkillHub 输出契约（schema_version 1.0）的 JSON：
{{
  "schema_version": "1.0",
  "case": {{
    "service": "{case['service']}",
    "reference_date": "{case['reference_date']}",
    "profile_summary": "{case['profile_summary']}"
  }},
  "sources": {json.dumps([{k: s[k] for k in ("id", "filename", "source_type", "source_date", "currentness")} for s in case["sources"]], ensure_ascii=False)},
  "requirements": [
    {{
      "id": "R1",
      "item": "要求名称",
      "necessity": "required" | "conditional" | "optional",
      "condition": null,
      "applicability": "applies" | "not_applicable" | "unknown",
      "status": "ready" | "missing" | "expired" | "conflict" | "needs_confirmation" | "not_applicable",
      "matched_inventory_ids": ["I01"],
      "reason": "清晰判定理由（日期项必须写出基准日期与计算结果）",
      "evidence": [
        {{"source_id": "S1", "locator": "L1", "quote": "原文逐字片段"}}
      ]
    }}
  ],
  "actions": [
    {{
      "id": "T1",
      "action": "具体可执行的补救或出门前准备动作",
      "priority": "blocking" | "high" | "normal",
      "evidence": [
        {{"source_id": "S1", "locator": "L1", "quote": "原文逐字片段"}}
      ]
    }}
  ],
  "overall_status": "ready" | "not_ready" | "needs_confirmation",
  "questions": ["若有待确认项，列出最多5个明确澄清问题；无则 []"],
  "limitations": [
    "本核验基于用户于 {case['reference_date']} 提供的文本，不代表最终官方最新修订，请以当地政务网或现场窗口审核为准。",
    "本工具全程只读且离线运行，不代办预约或提交，最终受理结果由受理机构工作人员现场审核决定。"
  ],
  "plain_language_summary_zh": "一句话大白话结论（让长辈或办事人一眼看懂能不能出门、差什么）",
  "plain_language_steps_zh": [
    "第1步：……（保留精确资格、材料份数/原件与时限）"
  ],
  "bilingual_summary_en": "One-sentence plain English verdict (empty string if plain_zh mode)",
  "bilingual_steps_en": [
    "Step 1: ... (preserve exact eligibility, document format, and deadlines; empty list if plain_zh mode)"
  ]
}}"""
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]
