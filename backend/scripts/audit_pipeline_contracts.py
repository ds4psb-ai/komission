#!/usr/bin/env python
"""
Pipeline Contract Audit (read-only)

Checks:
- Outlier status enum consistency (model vs schema vs frontend)
- analysis_status values used in code vs canonical list
- curation rule condition keys vs feature extractor keys (optional DB)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
sys.path.append(str(BACKEND_ROOT))

from app.models import OutlierItemStatus as ModelOutlierStatus  # noqa: E402
from app.schemas.evidence import OutlierItemStatus as SchemaOutlierStatus  # noqa: E402

CANONICAL_ANALYSIS_STATUS = {
    "pending",
    "approved",
    "analyzing",
    "completed",
    "comments_pending_review",
    "comments_failed",
    "comments_ready",
    "skipped",
}


def _enum_values(enum_cls) -> Set[str]:
    return {e.value for e in enum_cls}


def _find_interface_block(text: str, interface_name: str) -> str:
    lines = text.splitlines()
    in_block = False
    brace_depth = 0
    block_lines: List[str] = []

    for line in lines:
        if not in_block:
            if re.search(rf"\\binterface\\s+{re.escape(interface_name)}\\b", line):
                in_block = True
                brace_depth += line.count("{") - line.count("}")
                block_lines.append(line)
            continue

        block_lines.append(line)
        brace_depth += line.count("{") - line.count("}")
        if brace_depth <= 0:
            break

    return "\n".join(block_lines)


def _extract_ts_union_values(block: str, field_name: str) -> Set[str]:
    pattern = re.compile(rf"\\b{re.escape(field_name)}\\b\\s*:\\s*([^;]+);")
    match = pattern.search(block)
    if not match:
        return set()
    return set(re.findall(r"'([^']+)'", match.group(1)))


_ANALYSIS_STATUS_PATTERN = re.compile(
    r"(?:\banalysis_status\b\s*=|['\"]analysis_status['\"]\s*:)\s*['\"]([a-z_]+)['\"]"
)


def _collect_analysis_status_values(root: Path) -> Set[str]:
    values: Set[str] = set()
    for path in root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in _ANALYSIS_STATUS_PATTERN.finditer(text):
            values.add(match.group(1))
    return values


def _extract_feature_keys(source_path: Path) -> Set[str]:
    text = source_path.read_text(encoding="utf-8")
    keys = set(re.findall(r"features\[(?:'|\")([^'\"]+)(?:'|\")\]", text))
    return keys


async def _fetch_rule_condition_keys(database_url: str) -> Set[str]:
    from sqlalchemy import select  # noqa: E402
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
    from sqlalchemy.orm import sessionmaker  # noqa: E402

    from app.models import CurationRule  # noqa: E402

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    keys: Set[str] = set()

    async with async_session() as db:
        result = await db.execute(select(CurationRule.conditions))
        for conditions in result.scalars().all():
            if isinstance(conditions, dict):
                keys.update(conditions.keys())

    await engine.dispose()
    return keys


def _report_section(title: str, items: Iterable[str]) -> bool:
    print(f"\n== {title} ==")
    has_issue = False
    for item in items:
        has_issue = True
        print(f"- {item}")
    if not has_issue:
        print("- OK")
    return has_issue


async def main() -> int:
    parser = argparse.ArgumentParser(description="Audit pipeline contracts")
    parser.add_argument("--with-db", action="store_true", help="Check rules vs features using DATABASE_URL")
    parser.add_argument("--fail-on-issue", action="store_true", help="Exit non-zero if issues found")
    args = parser.parse_args()

    issues: List[str] = []

    # Enum alignment checks
    model_statuses = _enum_values(ModelOutlierStatus)
    schema_statuses = _enum_values(SchemaOutlierStatus)
    if model_statuses != schema_statuses:
        model_statuses_lower = {value.lower() for value in model_statuses}
        if model_statuses_lower == schema_statuses:
            print(
                "NOTE: OutlierItemStatus differs only by case "
                f"(model={sorted(model_statuses)} vs schema={sorted(schema_statuses)})"
            )
        else:
            issues.append(
                "OutlierItemStatus mismatch "
                f"(model={sorted(model_statuses)} vs schema={sorted(schema_statuses)})"
            )

    frontend_api = REPO_ROOT / "frontend" / "src" / "lib" / "api.ts"
    if frontend_api.exists():
        text = frontend_api.read_text(encoding="utf-8")
        block = _find_interface_block(text, "OutlierItem") or text
        ts_statuses = _extract_ts_union_values(block, "status")
        ts_analysis_statuses = _extract_ts_union_values(block, "analysis_status")
        if ts_statuses and ts_statuses != schema_statuses:
            issues.append(
                f"OutlierItem status mismatch (schema={sorted(schema_statuses)} vs frontend={sorted(ts_statuses)})"
            )
        if ts_analysis_statuses and ts_analysis_statuses != CANONICAL_ANALYSIS_STATUS:
            issues.append(
                "analysis_status mismatch (frontend vs canonical): "
                f"frontend={sorted(ts_analysis_statuses)} canonical={sorted(CANONICAL_ANALYSIS_STATUS)}"
            )
    else:
        issues.append("frontend/src/lib/api.ts not found (status alignment skipped)")

    # analysis_status values in code
    analysis_values = _collect_analysis_status_values(REPO_ROOT / "backend" / "app")
    unknown_statuses = analysis_values - CANONICAL_ANALYSIS_STATUS
    if unknown_statuses:
        issues.append(
            f"Unknown analysis_status values in code: {sorted(unknown_statuses)}"
        )

    _report_section("Enum and Status Checks", issues)

    # Feature vs rule condition keys (optional)
    feature_keys = _extract_feature_keys(BACKEND_ROOT / "app" / "services" / "curation_service.py")
    if args.with_db:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            _report_section("Rule/Feature Checks", ["DATABASE_URL not set; skipping DB checks"])
        else:
            rule_keys = await _fetch_rule_condition_keys(database_url)
            missing_keys = {key for key in rule_keys if key not in feature_keys}
            rule_issues = []
            if missing_keys:
                rule_issues.append(
                    "Rule conditions contain keys not produced by extract_features_from_vdg: "
                    + ", ".join(sorted(missing_keys))
                )
            _report_section("Rule/Feature Checks", rule_issues)
            if rule_issues:
                issues.extend(rule_issues)
    else:
        _report_section("Rule/Feature Checks", ["Skipped (use --with-db to enable)"])

    if args.fail_on_issue and issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
