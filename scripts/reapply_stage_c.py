"""Re-apply deterministic Stage C (verifier + official SkillHub --strict) to saved Spark-X2.6-4B traces without re-querying LLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plaincivic.runner import load_cases, summarize_run  # noqa: E402
from plaincivic.spark_client import extract_json_object  # noqa: E402
from plaincivic.verifier import (  # noqa: E402
    audit_clause_survival,
    check_verbatim_quotes,
    normalize_and_repair_readiness,
    render_readiness_markdown,
    run_skillhub_strict_validator,
)

GOLD = json.loads((ROOT / "gold" / "gold.json").read_text(encoding="utf-8"))["cases"]
CASES = {c["case_id"]: c for c in load_cases()}


def reapply_run(run_name: str) -> None:
    run_dir = ROOT / "runs" / run_name
    if not run_dir.exists():
        return
    traces = []
    for cid in sorted(CASES.keys()):
        tp = run_dir / cid / "trace.json"
        if not tp.exists():
            continue
        tr = json.loads(tp.read_text(encoding="utf-8"))
        if tr.get("mode") != "skill_v2":
            traces.append(tr)
            continue
        case = CASES[cid]
        raw_stage_b = extract_json_object((tr.get("stage_b_spark") or {}).get("content", "")) or {}
        stage_a_json = tr.get("stage_a_parsed") or {}
        repaired_doc, repairs = normalize_and_repair_readiness(raw_stage_b, case, stage_a_json)
        jp = run_dir / cid / "readiness.json"
        jp.write_text(json.dumps(repaired_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        post_strict = run_skillhub_strict_validator(jp)
        post_quotes = check_verbatim_quotes(repaired_doc, case)
        md = render_readiness_markdown(
            case=case,
            doc=repaired_doc,
            plain_zh_summary=tr.get("plain_language_summary_zh", ""),
            plain_zh_steps=tr.get("plain_language_steps_zh", []),
            bilingual_en_summary=tr.get("bilingual_summary_en", ""),
            bilingual_en_steps=tr.get("bilingual_steps_en", []),
            strict_result=post_strict,
        )
        (run_dir / cid / "readiness-report.md").write_text(md, encoding="utf-8")
        audit = audit_clause_survival(
            case=case,
            gold_case=GOLD[cid],
            readiness_doc=repaired_doc,
            plain_zh_steps=tr.get("plain_language_steps_zh", []),
            bilingual_en_steps=tr.get("bilingual_steps_en", []),
            plain_zh_summary=tr.get("plain_language_summary_zh", ""),
            bilingual_en_summary=tr.get("bilingual_summary_en", ""),
        )
        tr["stage_c_repairs"] = repairs
        tr["skillhub_strict"] = post_strict
        tr["quote_check"] = post_quotes
        tr["audit"] = audit
        tp.write_text(json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")
        traces.append(tr)
    if traces:
        s = summarize_run(run_name, traces)
        (run_dir / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"=== RE-APPLIED {run_name} ===")
        print(json.dumps(s, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    for name in ("skill_v2_none", "skill_v2_low", "skill_v2_high"):
        reapply_run(name)
