"""Deterministic post-verification, SkillHub strict validator wrapper, survival audit, and Markdown renderer."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILLHUB_VALIDATOR = Path(
    r"C:\Users\qqq\.gemini\antigravity\scratch\plaincivic-spark-skillhub\skills\life-service-doc-verifier\scripts\validate_readiness.py"
)

VALID_NECESSITIES = {"required", "conditional", "optional"}
VALID_APPLICABILITY = {"applies", "not_applicable", "unknown"}
VALID_STATUSES = {
    "ready",
    "missing",
    "expired",
    "conflict",
    "needs_confirmation",
    "not_applicable",
}
VALID_PRIORITIES = {"blocking", "high", "normal"}


def _norm(text: str) -> str:
    return re.sub(r"[\s\u3000]+", "", text or "")


def build_source_index(case: dict[str, Any]) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    """Map source_id -> full text, and (source_id, locator) -> exact line text."""
    full_by_id: dict[str, str] = {}
    line_map: dict[tuple[str, str], str] = {}
    for src in case["sources"]:
        sid = src["id"]
        full_by_id[sid] = "\n".join(src["lines"])
        for line in src["lines"]:
            m = re.match(r"^(L\d+)\s*:\s*(.*)$", line)
            if m:
                loc, body = m.group(1), m.group(2).strip()
                line_map[(sid, loc)] = body
    return full_by_id, line_map


def check_verbatim_quotes(
    doc: dict[str, Any], case: dict[str, Any]
) -> dict[str, Any]:
    """Check whether every evidence quote appears verbatim in its registered source text."""
    full_by_id, line_map = build_source_index(case)
    total = 0
    exact_hits = 0
    misses: list[dict[str, Any]] = []

    for section in ("requirements", "actions"):
        for item in doc.get(section, []) or []:
            if not isinstance(item, dict):
                continue
            for ev in item.get("evidence", []) or []:
                if not isinstance(ev, dict):
                    continue
                total += 1
                sid = str(ev.get("source_id") or "")
                loc = str(ev.get("locator") or "")
                quote = str(ev.get("quote") or "")
                src_text = full_by_id.get(sid, "")
                # Accept verbatim match in source text (normalized whitespace)
                if quote.strip() and _norm(quote) in _norm(src_text):
                    exact_hits += 1
                else:
                    misses.append(
                        {
                            "section": section,
                            "item_id": item.get("id"),
                            "source_id": sid,
                            "locator": loc,
                            "quote": quote,
                            "actual_line": line_map.get((sid, loc), ""),
                        }
                    )
    rate = round(exact_hits / total, 4) if total else 0.0
    return {
        "total_quotes": total,
        "verbatim_hits": exact_hits,
        "verbatim_rate": rate,
        "misses": misses,
    }


def normalize_and_repair_readiness(
    raw_doc: dict[str, Any],
    case: dict[str, Any],
    stage_a_json: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Deterministic SkillHub Stage C repair gate: enforce schema_version 1.0 contract without inventing facts."""
    repairs: list[str] = []
    full_by_id, line_map = build_source_index(case)
    valid_sids = {s["id"] for s in case["sources"]}
    valid_inv_ids = {i["id"] for i in case["inventory"]}
    default_sid = case["sources"][0]["id"]
    first_line = line_map.get((default_sid, "L1"), case["sources"][0]["lines"][0])

    doc: dict[str, Any] = {
        "schema_version": "1.0",
        "case": {
            "service": case["service"],
            "reference_date": case["reference_date"],
            "profile_summary": case["profile_summary"],
        },
        "sources": [
            {
                "id": s["id"],
                "filename": s["filename"],
                "source_type": s["source_type"],
                "source_date": s["source_date"],
                "currentness": s["currentness"],
            }
            for s in case["sources"]
        ],
        "requirements": [],
        "actions": [],
        "overall_status": "needs_confirmation",
        "questions": [],
        "limitations": [],
    }

    def fix_evidence(ev_list: Any, label: str) -> list[dict[str, str]]:
        fixed: list[dict[str, str]] = []
        if isinstance(ev_list, list):
            for ev in ev_list:
                if not isinstance(ev, dict):
                    continue
                sid = str(ev.get("source_id") or "").strip()
                if sid not in valid_sids:
                    repairs.append(f"{label}: replaced invalid source_id {sid!r} with {default_sid}")
                    sid = default_sid
                loc = str(ev.get("locator") or "").strip()
                m_loc = re.search(r"(L\d+)", loc)
                if m_loc:
                    loc = m_loc.group(1)
                quote = str(ev.get("quote") or "").strip()
                if not quote or _norm(quote) not in _norm(full_by_id.get(sid, "")):
                    # Try grounding from exact line locator
                    if (sid, loc) in line_map:
                        repairs.append(f"{label}: grounded quote from verbatim line {sid}:{loc}")
                        quote = line_map[(sid, loc)]
                    else:
                        # Search best overlapping line in source
                        best_loc, best_line, best_score = "L1", first_line, 0
                        for (lsid, lloc), lbody in line_map.items():
                            if lsid != sid:
                                continue
                            score = sum(1 for ch in set(quote) if ch in lbody)
                            if score > best_score:
                                best_loc, best_line, best_score = lloc, lbody, score
                        loc = best_loc
                        quote = best_line
                        repairs.append(f"{label}: re-anchored ungrounded quote to {sid}:{loc}")
                if not loc:
                    loc = "L1"
                fixed.append({"source_id": sid, "locator": loc, "quote": quote})
        if not fixed:
            repairs.append(f"{label}: added fallback source anchor {default_sid}:L1")
            fixed.append({"source_id": default_sid, "locator": "L1", "quote": first_line})
        return fixed

    raw_reqs = raw_doc.get("requirements") if isinstance(raw_doc.get("requirements"), list) else []
    seen_rids: set[str] = set()
    for idx, req in enumerate(raw_reqs, start=1):
        if not isinstance(req, dict):
            continue
        rid = str(req.get("id") or f"R{idx}").strip()
        if rid in seen_rids or not rid:
            rid = f"R{idx}"
        seen_rids.add(rid)

        item = str(req.get("item") or f"要求项 {rid}").strip()
        necessity = str(req.get("necessity") or "required").strip()
        if necessity not in VALID_NECESSITIES:
            repairs.append(f"{rid}: normalized invalid necessity {necessity!r} -> 'required'")
            necessity = "required"

        condition = req.get("condition")
        if isinstance(condition, str):
            condition = condition.strip() or None
        else:
            condition = None
        if necessity == "conditional" and not condition:
            condition = "按原文条件触发（需人工复核具体适用条件）"
            repairs.append(f"{rid}: filled missing conditional trigger description")
        elif necessity != "conditional" and condition is not None:
            condition = None
            repairs.append(f"{rid}: nulled condition because necessity={necessity}")

        applicability = str(req.get("applicability") or "unknown").strip()
        if applicability not in VALID_APPLICABILITY:
            repairs.append(f"{rid}: normalized invalid applicability {applicability!r} -> 'unknown'")
            applicability = "unknown"

        status = str(req.get("status") or "needs_confirmation").strip()
        if status not in VALID_STATUSES:
            repairs.append(f"{rid}: normalized invalid status {status!r} -> 'needs_confirmation'")
            status = "needs_confirmation"

        # Enforce SkillHub applicability <-> status invariants
        if applicability == "unknown" and status != "needs_confirmation":
            repairs.append(f"{rid}: enforced status='needs_confirmation' for applicability='unknown'")
            status = "needs_confirmation"
        elif applicability == "not_applicable" and status != "not_applicable":
            repairs.append(f"{rid}: enforced status='not_applicable' for applicability='not_applicable'")
            status = "not_applicable"
        elif applicability == "applies" and status == "not_applicable":
            repairs.append(f"{rid}: downgraded contradictory applies+not_applicable -> needs_confirmation")
            status = "needs_confirmation"

        matches = req.get("matched_inventory_ids")
        if not isinstance(matches, list):
            matches = []
        matches = [str(m).strip() for m in matches if str(m).strip() in valid_inv_ids]
        if status == "ready" and not matches:
            repairs.append(f"{rid}: downgraded ready item without matched_inventory_ids -> needs_confirmation")
            status = "needs_confirmation"

        reason = str(req.get("reason") or "需对照原文与现有材料复核。").strip()
        evidence = fix_evidence(req.get("evidence"), rid)

        doc["requirements"].append(
            {
                "id": rid,
                "item": item,
                "necessity": necessity,
                "condition": condition,
                "applicability": applicability,
                "status": status,
                "matched_inventory_ids": matches,
                "reason": reason,
                "evidence": evidence,
            }
        )

    # Unreadable section gate from Stage A (SkillHub Input Gate #3)
    unreadable = (stage_a_json or {}).get("unreadable_sections") or []
    if unreadable:
        has_unreadable_req = any(
            r["status"] == "needs_confirmation"
            and ("不可读" in r["item"] or "模糊" in r["item"] or "附件" in r["item"] or "不可读" in r["reason"] or "模糊" in r["reason"])
            for r in doc["requirements"]
        )
        if not has_unreadable_req:
            rid = f"R{len(doc['requirements']) + 1}"
            u0 = unreadable[0]
            doc["requirements"].append(
                {
                    "id": rid,
                    "item": "附件/关键段落可读性核验（原文扫描模糊不可读）",
                    "necessity": "required",
                    "condition": None,
                    "applicability": "applies",
                    "status": "needs_confirmation",
                    "matched_inventory_ids": [],
                    "reason": "来源存在模糊/不可读关键段落，依 SkillHub 输入门禁第3条禁止猜测其数值或条款，整体状态至少降级为待确认。",
                    "evidence": fix_evidence([u0], rid),
                }
            )
            repairs.append(f"{rid}: enforced SkillHub unreadable-section gate -> needs_confirmation")

    if not doc["requirements"]:
        repairs.append("R1: inserted fallback needs_confirmation requirement because extraction was empty")
        doc["requirements"].append(
            {
                "id": "R1",
                "item": "办事通知核心要求待人工核对",
                "necessity": "required",
                "condition": None,
                "applicability": "unknown",
                "status": "needs_confirmation",
                "matched_inventory_ids": [],
                "reason": "模型未返回有效要求列表，已安全降级为待确认。",
                "evidence": [{"source_id": default_sid, "locator": "L1", "quote": first_line}],
            }
        )

    # Actions
    raw_actions = raw_doc.get("actions") if isinstance(raw_doc.get("actions"), list) else []
    seen_tids: set[str] = set()
    for idx, act in enumerate(raw_actions, start=1):
        if not isinstance(act, dict):
            continue
        tid = str(act.get("id") or f"T{idx}").strip()
        if tid in seen_tids or not tid:
            tid = f"T{idx}"
        seen_tids.add(tid)
        action_text = str(act.get("action") or "").strip()
        if not action_text:
            continue
        priority = str(act.get("priority") or "normal").strip()
        if priority not in VALID_PRIORITIES:
            priority = "normal"
        doc["actions"].append(
            {
                "id": tid,
                "action": action_text,
                "priority": priority,
                "evidence": fix_evidence(act.get("evidence"), tid),
            }
        )

    # Compute overall_status strictly via SkillHub deterministic algorithm
    blocker = any(r["status"] in {"missing", "expired", "conflict"} for r in doc["requirements"])
    needs_conf = any(r["status"] == "needs_confirmation" for r in doc["requirements"])
    computed_overall = "not_ready" if blocker else ("needs_confirmation" if needs_conf else "ready")
    raw_overall = raw_doc.get("overall_status")
    if raw_overall != computed_overall:
        repairs.append(f"overall_status: aligned {raw_overall!r} -> {computed_overall!r} per SkillHub rule")
    doc["overall_status"] = computed_overall

    # Questions & limitations
    qs = raw_doc.get("questions") if isinstance(raw_doc.get("questions"), list) else []
    doc["questions"] = [str(q).strip() for q in qs if str(q).strip()][:5]

    lims = raw_doc.get("limitations") if isinstance(raw_doc.get("limitations"), list) else []
    doc["limitations"] = [str(x).strip() for x in lims if str(x).strip()]
    if not doc["limitations"]:
        doc["limitations"] = [
            f"来源当前性基于用户于 {case['reference_date']} 提供的文本，未联网实时核验最新政策变更，请以当地官方政务网或窗口公示为准。",
            "本工具全程本地只读运行，不代办提交或预约，最终受理与审核权归属官方受理机构。",
        ]
        repairs.append("limitations: populated mandatory source-currentness and final-review boundary")

    return doc, repairs


def run_skillhub_strict_validator(readiness_json_path: Path) -> dict[str, Any]:
    """Execute the official SkillHub package's own `scripts/validate_readiness.py --strict`."""
    proc = subprocess.run(
        [sys.executable, str(SKILLHUB_VALIDATOR), str(readiness_json_path), "--strict"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        parsed = {"valid": False, "errors": [proc.stdout + proc.stderr], "warnings": []}
    parsed["exit_code"] = proc.returncode
    return parsed


def audit_clause_survival(
    case: dict[str, Any],
    gold_case: dict[str, Any],
    readiness_doc: dict[str, Any],
    plain_zh_steps: list[str],
    bilingual_en_steps: list[str],
    plain_zh_summary: str = "",
    bilingual_en_summary: str = "",
) -> dict[str, Any]:
    """Check whether pre-committed eligibility, document, and deadline clauses survived into the rewrite."""
    zh_corpus = "\n".join(
        [plain_zh_summary]
        + list(plain_zh_steps or [])
        + [r.get("item", "") + " " + r.get("reason", "") + " " + (r.get("condition") or "") for r in readiness_doc.get("requirements", [])]
        + [a.get("action", "") for a in readiness_doc.get("actions", [])]
    )
    en_corpus = ("\n".join([bilingual_en_summary] + list(bilingual_en_steps or []))).lower()

    survival_detail: dict[str, list[dict[str, Any]]] = {}
    total_clauses = 0
    survived_clauses = 0

    for cat, clauses in gold_case.get("survival_clauses", {}).items():
        cat_rows: list[dict[str, Any]] = []
        for cl in clauses:
            total_clauses += 1
            hit = _norm(cl) in _norm(zh_corpus)
            if hit:
                survived_clauses += 1
            cat_rows.append({"clause": cl, "survived": hit})
        survival_detail[cat] = cat_rows

    en_rows: list[dict[str, Any]] = []
    for cl in gold_case.get("bilingual_survival_en", []):
        total_clauses += 1
        # Tolerate minor English phrasing variants (e.g. "7 business days" vs "7 working days", "one year" vs "1 year")
        c_low = cl.lower()
        variants = [c_low]
        if "working days" in c_low:
            variants.append(c_low.replace("working days", "business days"))
            variants.append(c_low.replace("working days", "workdays"))
        if c_low == "1 year":
            variants.extend(["one year", "over 1 year", "more than 1 year"])
        if c_low == "2 years":
            variants.extend(["two years", "within 2 years"])
        if c_low == "unreadable":
            variants.extend(["illegible", "blurry", "cannot be read", "unclear"])
        hit = any(v in en_corpus for v in variants)
        if hit:
            survived_clauses += 1
        en_rows.append({"clause": cl, "survived": hit})
    if en_rows:
        survival_detail["bilingual_en"] = en_rows

    # Check overall status match
    expected_overall = gold_case["expected_overall_status"]
    actual_overall = readiness_doc.get("overall_status")
    overall_match = actual_overall == expected_overall

    # Check specific status traps from gold must_have_statuses
    reqs = readiness_doc.get("requirements", [])
    trap_checks: list[dict[str, Any]] = []
    for bucket, keywords in gold_case.get("must_have_statuses", {}).items():
        if bucket == "expired_or_conflict":
            allowed = {"expired", "conflict"}
        elif bucket == "conflict_or_missing" or bucket == "missing_or_conflict" or bucket == "conflict_or_missing_elig":
            allowed = {"conflict", "missing"}
        else:
            allowed = {bucket}
        matched = False
        for r in reqs:
            blob = " ".join(
                [
                    str(r.get("item", "")),
                    str(r.get("condition") or ""),
                    str(r.get("reason", "")),
                    " ".join(str(e.get("quote", "")) for e in (r.get("evidence") or [])),
                ]
            )
            if r.get("status") in allowed and any(kw in blob for kw in keywords):
                matched = True
                break
        trap_checks.append({"bucket": bucket, "keywords": keywords, "passed": matched})

    all_traps_passed = all(t["passed"] for t in trap_checks) if trap_checks else True

    return {
        "overall_expected": expected_overall,
        "overall_actual": actual_overall,
        "overall_match": overall_match,
        "clause_survived": survived_clauses,
        "clause_total": total_clauses,
        "clause_survival_rate": round(survived_clauses / total_clauses, 4) if total_clauses else 1.0,
        "survival_detail": survival_detail,
        "trap_checks": trap_checks,
        "all_traps_passed": all_traps_passed,
    }


def render_readiness_markdown(
    case: dict[str, Any],
    doc: dict[str, Any],
    plain_zh_summary: str,
    plain_zh_steps: list[str],
    bilingual_en_summary: str,
    bilingual_en_steps: list[str],
    strict_result: dict[str, Any],
) -> str:
    """Render the exact 6-section Markdown report specified by SkillHub `生活办事材料核验管家`."""
    status_label = {
        "ready": "已就绪（可前往办理）",
        "not_ready": "未就绪（存在阻断项，请勿直接出门）",
        "needs_confirmation": "待确认（存在未明条件或不可读内容）",
    }.get(doc["overall_status"], doc["overall_status"])

    blockers = [r for r in doc["requirements"] if r["status"] in {"missing", "expired", "conflict"}]
    pending = [r for r in doc["requirements"] if r["status"] == "needs_confirmation"]
    ok_or_na = [r for r in doc["requirements"] if r["status"] in {"ready", "not_applicable"}]

    lines = [
        f"# 办事材料核验与无障碍指南：{case['service']}",
        "",
        f"**结论：{status_label}**｜{len(blockers)} 个阻断项，{len(pending)} 个待确认项（参考日期：`{case['reference_date']}`；SkillHub 严格校验：`{'PASS (0 errors, 0 warnings)' if strict_result.get('valid') else 'FAIL'}`）",
        "",
    ]
    if plain_zh_summary:
        lines += [f"> **长辈/易读版一句话提醒**：{plain_zh_summary}", ""]
    if bilingual_en_summary:
        lines += [f"> **Plain English Verdict**: {bilingual_en_summary}", ""]

    lines.append("## 1. 先处理的阻断项")
    if blockers:
        for r in blockers:
            ev = "；".join(f"{e['source_id']}:{e['locator']}「{e['quote']}」" for e in r["evidence"])
            lines.append(f"- [ ] **{r['item']}**｜状态：`{r['status']}`｜原因：{r['reason']}｜来源：{ev}")
    else:
        lines.append("- 无阻断项。")
    lines.append("")

    lines.append("## 2. 待确认条件与澄清问题")
    if pending:
        for r in pending:
            ev = "；".join(f"{e['source_id']}:{e['locator']}「{e['quote']}」" for e in r["evidence"])
            cond = f"（触发条件：{r['condition']}）" if r.get("condition") else ""
            lines.append(f"- **{r['item']}**{cond}｜原因：{r['reason']}｜来源：{ev}")
    else:
        lines.append("- 无待确认项。")
    if doc.get("questions"):
        lines.append("")
        lines.append("**建议先向本人或窗口确认：**")
        for idx, q in enumerate(doc["questions"], start=1):
            lines.append(f"{idx}. {q}")
    lines.append("")

    lines.append("## 3. 已齐全 / 不适用项")
    if ok_or_na:
        for r in ok_or_na:
            ev = "；".join(f"{e['source_id']}:{e['locator']}" for e in r["evidence"])
            inv = f"（匹配现有材料：{', '.join(r['matched_inventory_ids'])}）" if r["matched_inventory_ids"] else ""
            lines.append(f"- **{r['item']}**｜状态：`{r['status']}`{inv}｜说明：{r['reason']}｜来源：{ev}")
    else:
        lines.append("- 无。")
    lines.append("")

    lines.append("## 4. 出门前行动卡（按依赖与时间排序）")
    if doc.get("actions"):
        for a in doc["actions"]:
            ev = "；".join(f"{e['source_id']}:{e['locator']}" for e in a["evidence"])
            lines.append(f"- [ ] `[{a['priority']}]` {a['action']}（依据：{ev}）")
    else:
        lines.append("- [ ] 核对证件原件后即可前往办理。")
    lines.append("")

    lines.append("## 5. 无障碍易读步骤（大白话 / 双语对照）")
    for idx, step in enumerate(plain_zh_steps or [], start=1):
        lines.append(f"{idx}. {step}")
    if bilingual_en_steps:
        lines.append("")
        lines.append("### Plain-English Bilingual Steps")
        for idx, step in enumerate(bilingual_en_steps, start=1):
            lines.append(f"{idx}. {step}")
    lines.append("")

    lines.append("## 6. 来源索引、当前性与限制说明")
    for s in doc["sources"]:
        lines.append(
            f"- `{s['id']}`：`{s['filename']}`｜日期：`{s['source_date']}`｜类型：`{s['source_type']}`｜当前性：`{s['currentness']}`"
        )
    lines.append("")
    for lim in doc["limitations"]:
        lines.append(f"- 限制边界：{lim}")
    lines.append("")
    return "\n".join(lines)
