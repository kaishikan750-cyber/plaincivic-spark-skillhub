"""Unit tests verifying deterministic SkillHub Stage C repair gate and official validate_readiness.py --strict."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"C:\Users\qqq\.gemini\antigravity\scratch\plaincivic-spark-skillhub")
sys.path.insert(0, str(ROOT / "src"))

from plaincivic.verifier import (  # noqa: E402
    audit_clause_survival,
    check_verbatim_quotes,
    normalize_and_repair_readiness,
    run_skillhub_strict_validator,
)


def test_repair_and_official_strict_validator() -> None:
    case = json.loads((ROOT / "cases" / "C01_nia-work-residence-permit.json").read_text(encoding="utf-8"))
    gold = json.loads((ROOT / "gold" / "gold.json").read_text(encoding="utf-8"))["cases"]["C01"]

    # Intentionally flawed raw LLM output to prove Stage C repair gate catches schema/contract issues
    flawed = {
        "overall_status": "ready",  # Wrong! Should be not_ready because of expired & conflict items
        "requirements": [
            {
                "id": "R1",
                "item": "有效护照原件",
                "necessity": "required",
                "condition": "should be null",  # Contract violation!
                "applicability": "applies",
                "status": "ready",
                "matched_inventory_ids": ["I01"],
                "reason": "持有2029年到期护照原件",
                "evidence": [{"source_id": "S1", "locator": "L3", "quote": "non-verbatim paraphrased quote"}],
            },
            {
                "id": "R2",
                "item": "6个月内有效身体健康证明原件",
                "necessity": "conditional",
                "condition": "申请有效期1年以上居留证件",
                "applicability": "applies",
                "status": "expired",
                "matched_inventory_ids": ["I05"],
                "reason": "2026-03-10距2026-11-24超过8个月",
                "evidence": [{"source_id": "S1", "locator": "L6", "quote": "6个月内有效《身体健康证明》原件"}],
            },
            {
                "id": "R3",
                "item": "白底彩色免冠照片",
                "necessity": "required",
                "condition": None,
                "applicability": "applies",
                "status": "conflict",
                "matched_inventory_ids": ["I03"],
                "reason": "现有蓝底照片与白底要求冲突",
                "evidence": [{"source_id": "S1", "locator": "L4", "quote": "近期白底彩色免冠照片"}],
            },
            {
                "id": "R4",
                "item": "亲属关系证明",
                "necessity": "conditional",
                "condition": "有随迁家属一同申请",
                "applicability": "not_applicable",
                "status": "missing",  # Contract violation: not_applicable must have status=not_applicable
                "matched_inventory_ids": [],
                "reason": "单人申请无随迁家属",
                "evidence": [{"source_id": "S1", "locator": "L7", "quote": "有随迁家属一同申请"}],
            },
        ],
        "actions": [],
        "questions": [],
        "limitations": [],
    }

    repaired, repairs = normalize_and_repair_readiness(flawed, case)
    assert repaired["overall_status"] == "not_ready", f"Expected not_ready, got {repaired['overall_status']}"
    assert len(repairs) >= 4, f"Expected multiple repairs, got {repairs}"

    with tempfile.TemporaryDirectory() as td:
        jp = Path(td) / "readiness.json"
        jp.write_text(json.dumps(repaired, ensure_ascii=False, indent=2), encoding="utf-8")
        strict_res = run_skillhub_strict_validator(jp)
        assert strict_res["valid"] is True, f"SkillHub --strict failed: {strict_res}"
        assert strict_res["errors"] == [] and strict_res["warnings"] == []

    qres = check_verbatim_quotes(repaired, case)
    assert qres["verbatim_rate"] == 1.0, f"Expected 100% verbatim rate after repair, got {qres}"

    audit = audit_clause_survival(
        case=case,
        gold_case=gold,
        readiness_doc=repaired,
        plain_zh_steps=["入境30日内本人到场提交护照、工作许可、白底照片和6个月内体检原件（1年以上必带），受理回执15个工作日。"],
        bilingual_en_steps=["Apply in person within 30 days of entry with white-background photo and health certificate (required for over 1 year, valid within 6 months); processing up to 15 working days."],
    )
    assert audit["overall_match"] is True
    assert audit["clause_survival_rate"] == 1.0
    assert audit["all_traps_passed"] is True
    print("ALL VERIFIER + OFFICIAL SKILLHUB --STRICT UNIT TESTS PASSED!")


if __name__ == "__main__":
    test_repair_and_official_strict_validator()
