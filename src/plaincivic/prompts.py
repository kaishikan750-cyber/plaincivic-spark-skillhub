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
    """Baseline v1: direct single-pass prompt WITHOUT SkillHub extraction-first split or strict validator."""
    bilingual_hint = (
        "同时提供英文对照步骤（bilingual_steps_en）。"
        if case.get("mode") == "bilingual"
        else "无需英文，bilingual_steps_en 填 []。"
    )
    sys_msg = (
        "你是政务办事助手。请直接输出一个合法的 JSON 对象（不要输出多余解释或 Markdown 以外的文字）。"
    )
    user_msg = f"""参考日期：{case['reference_date']}
事项：{case['service']}
用户情况：{case['profile_summary']}

【办事通知原文】
{format_sources_block(case['sources'])}

【用户现有材料】
{format_inventory_block(case['inventory'])}

请输出 JSON：
- overall_status: "ready" | "not_ready" | "needs_confirmation"
- summary_zh: 一句话结论
- requirements: 数组，每项含 id, item, necessity("required"|"conditional"|"optional"), condition(无则为null), applicability("applies"|"not_applicable"|"unknown"), status("ready"|"missing"|"expired"|"conflict"|"needs_confirmation"|"not_applicable"), matched_inventory_ids, reason, evidence([{{source_id, locator, quote}}])
- actions: 数组，每项含 id, action, priority("blocking"|"high"|"normal"), evidence([{{source_id, locator, quote}}])
- plain_language_steps_zh: 3-5条通俗分步指南（保留资格、材料规格与截止时限）
- bilingual_steps_en: {bilingual_hint}
- questions: 待确认问题数组
- limitations: 局限说明数组
"""
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]


def build_stage_a_extraction_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    """SkillHub Stage A (Rule #1): Blind extraction from source notices BEFORE seeing user inventory."""
    sys_msg = """你正在执行 SkillHub 技能「生活办事材料核验管家」(v20260716.135124) 第1步【先提取要求，再查看现有材料】。
请简明直接地输出一个合法 JSON 对象（不要反复数字符数，不要输出额外解释）：
1. 你看不到用户材料，只能从原文提取正式要求，跳过纯标题行（如“【事项名称】”），严禁加入原文未写的材料。
2. 每项必须给出精确 source_id（如 "S1"）、locator（行号如 "L4"）和 quote（直接复制自该行的一段连续原文短句，切勿改写）。
3. `extracted_requirements` 提取所有可核验的资格条件、申请截止/前置时限、必备/条件材料、多源冲突项与不可读附件；一般性的“受理后审批工作日/收费标准/开放时间/不设截止日期”记入 `service_info_notes`。
4. 若 S1 与 S2 互相冲突，写入 `multi_source_conflicts` 并列双方，严禁自行选边。
5. 若原文有扫描模糊/不可读段落，写入 `unreadable_sections`，严禁猜测其中的金额或条款。"""

    user_msg = f"""事项：{case['service']}（参考日期：{case['reference_date']}）

【登记来源全文】
{format_sources_block(case['sources'])}

输出 JSON：
{{
  "extracted_requirements": [
    {{
      "id": "R1",
      "category": "eligibility" | "document" | "deadline" | "fee" | "unreadable",
      "item": "精炼要求名",
      "necessity": "required" | "conditional" | "optional",
      "condition": "仅 conditional 时填触发条件，否则 null",
      "constraints": "保留原文硬限定（如原件/复印件2份/白底/6个月内/30日内/7日前/15个工作日）",
      "source_id": "S1",
      "locator": "L2",
      "quote": "直接逐字复制自该行的原文片段"
    }}
  ],
  "multi_source_conflicts": [
    {{"topic": "冲突项", "side_a": {{"source_id": "S1", "locator": "L2", "quote": "原文"}}, "side_b": {{"source_id": "S2", "locator": "L2", "quote": "原文"}}}}
  ],
  "unreadable_sections": [
    {{"source_id": "S1", "locator": "L7", "quote": "原文不可读摘录"}}
  ],
  "service_info_notes": [
    {{"label": "办理时限/费用/窗口时间", "exact_text": "原文精确表述", "source_id": "S1", "locator": "L8"}}
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
    """SkillHub Stage B (Rules #2-#5): Compact readiness evaluation & accessible/bilingual rewrite."""
    is_bilingual = case.get("mode") == "bilingual"
    bilingual_rule = (
        "7. 【中英双语无障碍改写】：输出 4-5 条中文易读步骤 `plain_language_steps_zh` 和 4-5 条完整英文对照步骤 `bilingual_steps_en` + `bilingual_summary_en`。无论用户当前是否已满足某项条件，中文步骤与英文步骤中都必须完整保留原文所有关键资格门槛（如 1年以上 / over 1 year、毕业2年内 / within 2 years、本人到场 / in person）、材料规格（如 护照/passport、白底/white background、6个月内/within 6 months、行程安排/itinerary）和全部时限（如 入境30日内/within 30 days、届满7日前/7 days before expiry、15个工作日/15 working days、7个工作日/7 working days、2026年11月30日17:00/2026-11-30 17:00、附件B不可读/unreadable Annex B），严禁省略！"
        if is_bilingual
        else "7. 【中文无障碍易读改写】：输出 4-5 条大白话易读步骤 `plain_language_steps_zh`（适合老人大字与读屏朗读）。无论用户是否已满足，步骤中必须完整保留原文资格条件、原件/复印件份数、照片规格、有效期天数、免费/收费标准、窗口时间及截止时限（含“不设报名截止日期”）。`bilingual_summary_en` 填 \"\"，`bilingual_steps_en` 填 []。"
    )

    sys_msg = f"""你正在执行 SkillHub 技能「生活办事材料核验管家」(v20260716.135124) 第2–5步【条件解析→材料比对→状态计算→无障碍改写】。
请简明思考并直接输出合法 JSON（系统会自动补全 case/sources/完整原文引文/limitations 契约字段，无需重复抄写长引文，也不要数字符数）：
1. 【不替用户猜身份】：`applicability` 仅限 `"applies"` / `"not_applicable"` / `"unknown"`。
   - 用户画像明确排除（单人无随迁、成年非未成年、民营退休非国家工作人员、未婚非已婚）→ `applicability="not_applicable"`, `status="not_applicable"`。
   - 用户画像未说明关键身份或选择（如未说是否长期居住还是转诊、有无居住证）→ 严禁猜测！必须 `applicability="unknown"`, `status="needs_confirmation"`！
2. 【严格日期算术与状态区分】（基准日 `{case['reference_date']}`）：
   - 先算准确天数再比较：2026-11-01 到 2026-11-24 为 23 天，23 <= 30（未超期）；
   - 2026-11-29 距 2026-11-24 仅剩 5 天，5 < 7（已错过“届满7日前”提前申请期 → 标 `"expired"` 或 `"conflict"`）；
   - 用户已有但超期的文件（如 2026-03-10 体检报告超 6 个月、2026-10-01 体检单 54 天超 30 日）→ 必须标 `"expired"`（不要标 missing！）；
   - 居住登记 2026-08-15 距 2026-11-24 约 3 个月 < 半年 → 标 `"conflict"`；
   - 仅有手机照片缺原件、复印件份数不够、蓝底非白底 → 标 `"missing"` 或 `"conflict"`。
3. 【多源冲突】：若 Stage A 发现 S1 与 S2 冲突，必须在对应 requirement 标 `"status": "conflict"` 且 `evidence_refs` 同时引用双方行号（如 `["S1:L2", "S2:L2"]`），严禁自行选边！
4. 【不可读门禁】：若 Stage A 存在 `unreadable_sections`，必须建立一条 `status="needs_confirmation"` 的条目，禁止编造金额或条款。
5. 【契约硬约束】：`necessity=="conditional"` 必须有非空 `condition`，否则 `condition=null`；`status=="ready"` 必须填写至少一个 `matched_inventory_ids`（如 `["I01"]`）。一般性的审批工作日、收费/免收费、开放时间与“不设报名截止日期”写入 `plain_language_steps_zh`（及英文步骤），不要作为空匹配项放进 `requirements`。
6. 【整体状态铁律】：有任一 `missing`/`expired`/`conflict` → `"not_ready"`；否则有 `needs_confirmation` → `"needs_confirmation"`；否则 → `"ready"`。
{bilingual_rule}"""

    user_msg = f"""【案件】{case['service']}｜参考日期：{case['reference_date']}｜模式：{case['mode']}
【用户画像】{case['profile_summary']}
【现有材料】
{format_inventory_block(case['inventory'])}

【Stage A 盲提结果】
{json.dumps(stage_a_json, ensure_ascii=False)}

请直接输出 JSON：
{{
  "overall_status": "ready" | "not_ready" | "needs_confirmation",
  "requirements": [
    {{
      "id": "R1",
      "item": "要求名",
      "necessity": "required" | "conditional" | "optional",
      "condition": null,
      "applicability": "applies" | "not_applicable" | "unknown",
      "status": "ready" | "missing" | "expired" | "conflict" | "needs_confirmation" | "not_applicable",
      "matched_inventory_ids": ["I01"],
      "reason": "简明判定理由与日期计算",
      "evidence_refs": ["S1:L2"]
    }}
  ],
  "actions": [
    {{"id": "T1", "action": "出门前补救或准备动作", "priority": "blocking" | "high" | "normal", "evidence_refs": ["S1:L6"]}}
  ],
  "questions": ["最多3个待澄清问题，无则 []"],
  "plain_language_summary_zh": "一句话大白话结论",
  "plain_language_steps_zh": ["第1步：...", "第2步：..."],
  "bilingual_summary_en": "",
  "bilingual_steps_en": []
}}"""
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_msg},
    ]
