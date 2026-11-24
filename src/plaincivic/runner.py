"""End-to-end runner for Baseline v1 and SkillHub-guided PlainCivic v2 on local Spark-X2.6-4B."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from .prompts import (
    build_baseline_v1_messages,
    build_stage_a_extraction_messages,
    build_stage_b_readiness_and_rewrite_messages,
)
from .spark_client import LocalSparkClient, extract_json_object
from .verifier import (
    audit_clause_survival,
    check_verbatim_quotes,
    normalize_and_repair_readiness,
    render_readiness_markdown,
    run_skillhub_strict_validator,
)

ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "cases"
GOLD_PATH = ROOT / "gold" / "gold.json"
RUNS_DIR = ROOT / "runs"


def load_cases(case_filter: set[str] | None = None) -> list[dict[str, Any]]:
    cases = []
    for p in sorted(CASES_DIR.glob("C*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if case_filter and data["case_id"] not in case_filter:
            continue
        cases.append(data)
    return cases


def run_baseline_case(
    client: LocalSparkClient,
    case: dict[str, Any],
    gold_case: dict[str, Any],
    out_dir: Path,
    thinking_mode: str = "low",
) -> dict[str, Any]:
    cid = case["case_id"]
    case_dir = out_dir / cid
    case_dir.mkdir(parents=True, exist_ok=True)

    msgs = build_baseline_v1_messages(case)
    resp = client.chat(msgs, thinking_mode=thinking_mode, max_tokens=5120, seed=42)
    parsed = extract_json_object(resp.content) or {}

    # Save raw un-repaired JSON to test whether Baseline v1 passes SkillHub --strict natively
    raw_readiness = {
        "schema_version": parsed.get("schema_version", "1.0"),
        "case": parsed.get(
            "case",
            {
                "service": case["service"],
                "reference_date": case["reference_date"],
                "profile_summary": case["profile_summary"],
            },
        ),
        "sources": parsed.get(
            "sources",
            [
                {k: s[k] for k in ("id", "filename", "source_type", "source_date", "currentness")}
                for s in case["sources"]
            ],
        ),
        "requirements": parsed.get("requirements", []),
        "actions": parsed.get("actions", []),
        "overall_status": parsed.get("overall_status", ""),
        "questions": parsed.get("questions", []),
        "limitations": parsed.get("limitations", []),
    }
    raw_json_path = case_dir / "readiness.json"
    raw_json_path.write_text(json.dumps(raw_readiness, ensure_ascii=False, indent=2), encoding="utf-8")

    strict_res = run_skillhub_strict_validator(raw_json_path)
    quote_res = check_verbatim_quotes(raw_readiness, case)
    survival_res = audit_clause_survival(
        case=case,
        gold_case=gold_case,
        readiness_doc=raw_readiness,
        plain_zh_steps=parsed.get("plain_language_steps_zh") or [],
        bilingual_en_steps=parsed.get("bilingual_steps_en") or [],
        plain_zh_summary=parsed.get("summary_zh") or "",
        bilingual_en_summary="",
    )

    trace = {
        "mode": "baseline_v1",
        "thinking_mode": thinking_mode,
        "case_id": cid,
        "spark_call": resp.to_dict(),
        "parsed_ok": bool(parsed),
        "skillhub_strict": strict_res,
        "quote_check": quote_res,
        "audit": survival_res,
    }
    (case_dir / "trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    return trace


def run_skill_v2_case(
    client: LocalSparkClient,
    case: dict[str, Any],
    gold_case: dict[str, Any],
    out_dir: Path,
    thinking_mode: str = "low",
) -> dict[str, Any]:
    cid = case["case_id"]
    case_dir = out_dir / cid
    case_dir.mkdir(parents=True, exist_ok=True)

    # Stage A: Blind extraction from source notices (SkillHub Rule #1)
    msgs_a = build_stage_a_extraction_messages(case)
    max_tok_a = 2048 if thinking_mode == "none" else (3584 if thinking_mode == "low" else 5120)
    resp_a = client.chat(msgs_a, thinking_mode=thinking_mode, max_tokens=max_tok_a, seed=42)
    stage_a_json = extract_json_object(resp_a.content) or {"extracted_requirements": [], "multi_source_conflicts": [], "unreadable_sections": []}

    # Stage B: Condition resolution, reference-date arithmetic, inventory matching, plain-language & bilingual rewrite
    msgs_b = build_stage_b_readiness_and_rewrite_messages(case, stage_a_json)
    max_tok_b = 3072 if thinking_mode == "none" else (4608 if thinking_mode == "low" else 6144)
    resp_b = client.chat(msgs_b, thinking_mode=thinking_mode, max_tokens=max_tok_b, seed=42)
    raw_stage_b = extract_json_object(resp_b.content) or {}
    stage_b_retried = False
    if not raw_stage_b:
        # Honest fallback retry (e.g. if reasoning-budget cutoff emitted truncated prose instead of JSON)
        stage_b_retried = True
        resp_b = client.chat(msgs_b, thinking_mode="none", max_tokens=3072, seed=43)
        raw_stage_b = extract_json_object(resp_b.content) or {}

    # Measure raw pre-repair Stage A verbatim quote rate & Stage B strict validity honestly
    stage_a_as_ev = {
        "requirements": [
            {
                "id": r.get("id"),
                "evidence": [{"source_id": r.get("source_id"), "locator": r.get("locator"), "quote": r.get("quote")}],
            }
            for r in (stage_a_json.get("extracted_requirements") or [])
            if isinstance(r, dict)
        ]
    }
    pre_quotes = check_verbatim_quotes(stage_a_as_ev, case)

    pre_repair_path = case_dir / "readiness_pre_repair.json"
    pre_repair_doc = {
        k: raw_stage_b.get(k)
        for k in ("schema_version", "case", "sources", "requirements", "actions", "overall_status", "questions", "limitations")
        if k in raw_stage_b
    }
    pre_repair_path.write_text(json.dumps(pre_repair_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    pre_strict = run_skillhub_strict_validator(pre_repair_path)

    # Stage C: Deterministic SkillHub contract repair & downgrade gate
    repaired_doc, repairs = normalize_and_repair_readiness(raw_stage_b, case, stage_a_json)
    final_json_path = case_dir / "readiness.json"
    final_json_path.write_text(json.dumps(repaired_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    post_strict = run_skillhub_strict_validator(final_json_path)
    post_quotes = check_verbatim_quotes(repaired_doc, case)

    plain_zh_summary = str(raw_stage_b.get("plain_language_summary_zh") or "").strip()
    plain_zh_steps = [str(s).strip() for s in (raw_stage_b.get("plain_language_steps_zh") or []) if str(s).strip()]
    bilingual_en_summary = str(raw_stage_b.get("bilingual_summary_en") or "").strip()
    bilingual_en_steps = [str(s).strip() for s in (raw_stage_b.get("bilingual_steps_en") or []) if str(s).strip()]

    md_report = render_readiness_markdown(
        case=case,
        doc=repaired_doc,
        plain_zh_summary=plain_zh_summary,
        plain_zh_steps=plain_zh_steps,
        bilingual_en_summary=bilingual_en_summary,
        bilingual_en_steps=bilingual_en_steps,
        strict_result=post_strict,
    )
    (case_dir / "readiness-report.md").write_text(md_report, encoding="utf-8")

    survival_res = audit_clause_survival(
        case=case,
        gold_case=gold_case,
        readiness_doc=repaired_doc,
        plain_zh_steps=plain_zh_steps,
        bilingual_en_steps=bilingual_en_steps,
        plain_zh_summary=plain_zh_summary,
        bilingual_en_summary=bilingual_en_summary,
    )

    trace = {
        "mode": "skill_v2",
        "thinking_mode": thinking_mode,
        "case_id": cid,
        "stage_a_spark": resp_a.to_dict(),
        "stage_a_parsed": stage_a_json,
        "stage_b_spark": resp_b.to_dict(),
        "stage_b_parsed_ok": bool(raw_stage_b),
        "stage_b_retried_no_think": stage_b_retried,
        "plain_language_summary_zh": plain_zh_summary,
        "plain_language_steps_zh": plain_zh_steps,
        "bilingual_summary_en": bilingual_en_summary,
        "bilingual_steps_en": bilingual_en_steps,
        "pre_repair_strict": pre_strict,
        "pre_repair_quotes": pre_quotes,
        "stage_c_repairs": repairs,
        "skillhub_strict": post_strict,
        "quote_check": post_quotes,
        "audit": survival_res,
        "total_wall_seconds": round(resp_a.wall_seconds + resp_b.wall_seconds, 3),
        "total_completion_tokens": resp_a.completion_tokens + resp_b.completion_tokens,
    }
    (case_dir / "trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    return trace


def summarize_run(run_name: str, traces: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(traces)
    if n == 0:
        return {}
    overall_ok = sum(1 for t in traces if t["audit"]["overall_match"])
    traps_ok = sum(1 for t in traces if t["audit"]["all_traps_passed"])
    strict_ok = sum(1 for t in traces if t["skillhub_strict"].get("valid"))
    pre_strict_ok = sum(1 for t in traces if t.get("pre_repair_strict", t["skillhub_strict"]).get("valid"))
    clause_hit = sum(t["audit"]["clause_survived"] for t in traces)
    clause_tot = sum(t["audit"]["clause_total"] for t in traces)
    q_hit = sum(t["quote_check"]["verbatim_hits"] for t in traces)
    q_tot = sum(t["quote_check"]["total_quotes"] for t in traces)
    pre_q_hit = sum(t.get("pre_repair_quotes", t["quote_check"])["verbatim_hits"] for t in traces)
    pre_q_tot = sum(t.get("pre_repair_quotes", t["quote_check"])["total_quotes"] for t in traces)
    total_sec = sum(t.get("total_wall_seconds", t.get("spark_call", {}).get("wall_seconds", 0)) for t in traces)
    total_tok = sum(t.get("total_completion_tokens", t.get("spark_call", {}).get("completion_tokens", 0)) for t in traces)

    return {
        "run_name": run_name,
        "cases": n,
        "overall_accuracy": round(overall_ok / n, 4),
        "overall_match_count": f"{overall_ok}/{n}",
        "trap_pass_rate": round(traps_ok / n, 4),
        "trap_pass_count": f"{traps_ok}/{n}",
        "clause_survival_rate": round(clause_hit / clause_tot, 4) if clause_tot else 0.0,
        "clause_survival_count": f"{clause_hit}/{clause_tot}",
        "pre_repair_strict_pass": f"{pre_strict_ok}/{n}",
        "post_repair_strict_pass": f"{strict_ok}/{n}",
        "pre_repair_verbatim_rate": round(pre_q_hit / pre_q_tot, 4) if pre_q_tot else 0.0,
        "post_repair_verbatim_rate": round(q_hit / q_tot, 4) if q_tot else 0.0,
        "avg_wall_seconds": round(total_sec / n, 2),
        "avg_completion_tokens": round(total_tok / n, 1),
        "avg_tokens_per_sec": round(total_tok / total_sec, 2) if total_sec > 0 else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--mode", choices=["baseline_v1", "skill_v2"], required=True)
    parser.add_argument("--thinking", choices=["none", "low", "high"], default="low")
    parser.add_argument("--cases", default="", help="Comma-separated case IDs, e.g. C01,C04")
    parser.add_argument("--resume", action="store_true", help="Reuse existing valid trace.json if present")
    args = parser.parse_args(argv)

    case_filter = {c.strip() for c in args.cases.split(",") if c.strip()} or None
    cases = load_cases(case_filter)
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))["cases"]

    client = LocalSparkClient(base_url=args.base_url)
    print(f"[HEALTH] {client.health()}", flush=True)

    run_name = f"{args.mode}_{args.thinking}"
    out_dir = RUNS_DIR / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    traces: list[dict[str, Any]] = []
    for case in cases:
        cid = case["case_id"]
        existing_trace = out_dir / cid / "trace.json"
        if args.resume and existing_trace.exists():
            tr = json.loads(existing_trace.read_text(encoding="utf-8"))
            if tr.get("parsed_ok") or tr.get("stage_b_parsed_ok"):
                print(f"==> [RESUME] Reusing {run_name}/{cid}", flush=True)
                traces.append(tr)
                continue
        t0 = time.perf_counter()
        print(f"==> Running {run_name} on {cid} ({case['slug']}) ...", flush=True)
        if args.mode == "baseline_v1":
            tr = run_baseline_case(client, case, gold[cid], out_dir, thinking_mode=args.thinking)
        else:
            tr = run_skill_v2_case(client, case, gold[cid], out_dir, thinking_mode=args.thinking)
        traces.append(tr)
        dt = time.perf_counter() - t0
        a = tr["audit"]
        strict_ok = tr["skillhub_strict"].get("valid")
        print(
            f"    [{cid}] overall={a['overall_actual']} (exp={a['overall_expected']}, match={a['overall_match']}) "
            f"| clauses={a['clause_survived']}/{a['clause_total']} | traps={a['all_traps_passed']} "
            f"| strict={strict_ok} | quotes={tr['quote_check']['verbatim_hits']}/{tr['quote_check']['total_quotes']} "
            f"| {dt:.1f}s",
            flush=True,
        )

    summary = summarize_run(run_name, traces)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== RUN SUMMARY ===", flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
