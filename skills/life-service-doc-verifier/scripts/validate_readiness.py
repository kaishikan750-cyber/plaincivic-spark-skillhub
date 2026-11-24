#!/usr/bin/env python3
"""Validate source-grounded life errand readiness JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


NECESSITIES = {"required", "conditional", "optional"}
APPLICABILITY = {"applies", "not_applicable", "unknown"}
STATUSES = {
    "ready",
    "missing",
    "expired",
    "conflict",
    "needs_confirmation",
    "not_applicable",
}
OVERALL_STATUSES = {"ready", "not_ready", "needs_confirmation"}
CURRENTNESS = {"user_provided_current", "officially_verified", "unknown", "stale"}
ACTION_PRIORITIES = {"blocking", "high", "normal"}


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_evidence(
    value: Any,
    path: str,
    source_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}.evidence must be a non-empty list")
        return
    for index, item in enumerate(value):
        item_path = f"{path}.evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        source_id = item.get("source_id")
        if source_id not in source_ids:
            errors.append(f"{item_path} has unknown source_id: {source_id!r}")
        if not _is_nonempty_text(item.get("locator")):
            errors.append(f"{item_path}.locator must be non-empty")
        if not _is_nonempty_text(item.get("quote")):
            errors.append(f"{item_path}.quote must be non-empty")


def validate_document(data: Any, strict: bool = False) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for one readiness document."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return ["document root must be an object"], warnings

    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    case = data.get("case")
    if not isinstance(case, dict):
        errors.append("case must be an object")
    else:
        for field in ("service", "reference_date", "profile_summary"):
            if not _is_nonempty_text(case.get(field)):
                errors.append(f"case.{field} must be non-empty")

    sources = data.get("sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        sources = []
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{path} must be an object")
            continue
        source_id = source.get("id")
        if not _is_nonempty_text(source_id):
            errors.append(f"{path}.id must be non-empty")
        elif source_id in source_ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            source_ids.add(source_id)
        for field in ("filename", "source_type", "source_date"):
            if not _is_nonempty_text(source.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        currentness = source.get("currentness")
        if currentness not in CURRENTNESS:
            errors.append(f"{path}.currentness must be one of {sorted(CURRENTNESS)}")
        elif currentness in {"unknown", "stale"}:
            warnings.append(f"{path} currentness is {currentness}; do not claim current official validity")

    requirements = data.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append("requirements must be a non-empty list")
        requirements = []

    requirement_ids: set[str] = set()
    blocker_found = False
    confirmation_found = False
    for index, requirement in enumerate(requirements):
        path = f"requirements[{index}]"
        if not isinstance(requirement, dict):
            errors.append(f"{path} must be an object")
            continue

        requirement_id = requirement.get("id")
        if not _is_nonempty_text(requirement_id):
            errors.append(f"{path}.id must be non-empty")
        elif requirement_id in requirement_ids:
            errors.append(f"duplicate requirement id: {requirement_id}")
        else:
            requirement_ids.add(requirement_id)

        if not _is_nonempty_text(requirement.get("item")):
            errors.append(f"{path}.item must be non-empty")
        if not _is_nonempty_text(requirement.get("reason")):
            errors.append(f"{path}.reason must be non-empty")

        necessity = requirement.get("necessity")
        if necessity not in NECESSITIES:
            errors.append(f"{path}.necessity must be one of {sorted(NECESSITIES)}")
        condition = requirement.get("condition")
        if necessity == "conditional" and not _is_nonempty_text(condition):
            errors.append(f"{path}.condition must describe the conditional trigger")
        if necessity != "conditional" and condition not in (None, ""):
            errors.append(f"{path}.condition must be null unless necessity is conditional")

        applicability = requirement.get("applicability")
        if applicability not in APPLICABILITY:
            errors.append(f"{path}.applicability must be one of {sorted(APPLICABILITY)}")
        status = requirement.get("status")
        if status not in STATUSES:
            errors.append(f"{path}.status must be one of {sorted(STATUSES)}")
        if applicability == "unknown" and status != "needs_confirmation":
            errors.append(f"{path}.status must be needs_confirmation when applicability is unknown")
        if applicability == "not_applicable" and status != "not_applicable":
            errors.append(f"{path}.status must be not_applicable when applicability is not_applicable")
        if applicability == "applies" and status == "not_applicable":
            errors.append(f"{path}.status cannot be not_applicable when applicability applies")

        matches = requirement.get("matched_inventory_ids")
        if not isinstance(matches, list):
            errors.append(f"{path}.matched_inventory_ids must be a list")
        elif status == "ready" and not matches:
            errors.append(f"{path}.matched_inventory_ids must identify evidence for a ready item")

        _validate_evidence(requirement.get("evidence"), path, source_ids, errors)
        blocker_found = blocker_found or status in {"missing", "expired", "conflict"}
        confirmation_found = confirmation_found or status == "needs_confirmation"

    actions = data.get("actions")
    if not isinstance(actions, list):
        errors.append("actions must be a list")
        actions = []
    action_ids: set[str] = set()
    for index, action in enumerate(actions):
        path = f"actions[{index}]"
        if not isinstance(action, dict):
            errors.append(f"{path} must be an object")
            continue
        action_id = action.get("id")
        if not _is_nonempty_text(action_id):
            errors.append(f"{path}.id must be non-empty")
        elif action_id in action_ids:
            errors.append(f"duplicate action id: {action_id}")
        else:
            action_ids.add(action_id)
        if not _is_nonempty_text(action.get("action")):
            errors.append(f"{path}.action must be non-empty")
        if action.get("priority") not in ACTION_PRIORITIES:
            errors.append(f"{path}.priority must be one of {sorted(ACTION_PRIORITIES)}")
        _validate_evidence(action.get("evidence"), path, source_ids, errors)

    expected_overall = "not_ready" if blocker_found else (
        "needs_confirmation" if confirmation_found else "ready"
    )
    overall = data.get("overall_status")
    if overall not in OVERALL_STATUSES:
        errors.append(f"overall_status must be one of {sorted(OVERALL_STATUSES)}")
    elif overall != expected_overall:
        errors.append(
            f"overall_status must be {expected_overall!r} for the requirement statuses, got {overall!r}"
        )

    for field in ("questions", "limitations"):
        value = data.get(field)
        if not isinstance(value, list) or any(not _is_nonempty_text(item) for item in value):
            errors.append(f"{field} must be a list of non-empty strings")
    if strict and not data.get("limitations"):
        warnings.append("limitations is empty; state the final-review and source-currentness boundary")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = json.loads(args.json_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        payload = {"valid": False, "errors": [f"cannot read JSON: {exc}"], "warnings": []}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    errors, warnings = validate_document(data, strict=args.strict)
    valid = not errors and (not args.strict or not warnings)
    print(json.dumps({"valid": valid, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())

