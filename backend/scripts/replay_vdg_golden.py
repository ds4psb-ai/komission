#!/usr/bin/env python
"""
Replay VDG golden fixtures and validate basic contracts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.services.curation_service import extract_features_from_vdg  # noqa: E402


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_outlier_item(item: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for key in ("video_url", "platform", "category"):
        if not item.get(key):
            issues.append(f"missing outlier field: {key}")
    return issues


def _validate_comments(comments: Any, min_count: int) -> List[str]:
    issues: List[str] = []
    if not isinstance(comments, list):
        return ["comments payload is not a list"]
    if len(comments) < min_count:
        issues.append(f"comment count {len(comments)} < min_comment_count {min_count}")
    return issues


def _validate_vdg(
    vdg: Dict[str, Any],
    required_keys: List[str],
    feature_ranges: Dict[str, List[float]],
) -> List[str]:
    issues: List[str] = []
    for key in required_keys:
        if key not in vdg:
            issues.append(f"missing vdg key: {key}")

    features = extract_features_from_vdg(vdg)
    for feature, bounds in feature_ranges.items():
        value = features.get(feature)
        if value is None:
            issues.append(f"missing feature: {feature}")
            continue
        if not isinstance(bounds, list) or len(bounds) != 2:
            issues.append(f"invalid bounds for feature {feature}: {bounds}")
            continue
        low, high = bounds
        if value < low or value > high:
            issues.append(f"feature {feature} out of range ({value} not in [{low}, {high}])")

    return issues


def _resolve_path(base: Path, rel_path: Optional[str]) -> Optional[Path]:
    if not rel_path:
        return None
    return (base / rel_path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay VDG golden fixtures")
    parser.add_argument(
        "--manifest",
        default=str(BACKEND_ROOT / "tests" / "fixtures" / "vdg_golden" / "manifest.json"),
        help="Path to manifest.json",
    )
    parser.add_argument("--fail-on-issue", action="store_true", help="Exit non-zero on issues")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return 1

    manifest = _load_json(manifest_path)
    base_dir = manifest_path.parent
    items = manifest.get("items", [])

    total = 0
    skipped = 0
    failed = 0

    for entry in items:
        total += 1
        entry_id = entry.get("id", f"item_{total}")
        if entry.get("enabled") is False:
            skipped += 1
            print(f"[SKIP] {entry_id}: {entry.get('reason', 'disabled')}")
            continue

        issues: List[str] = []
        outlier_path = _resolve_path(base_dir, entry.get("outlier_item_path"))
        comments_path = _resolve_path(base_dir, entry.get("comments_path"))
        vdg_path = _resolve_path(base_dir, entry.get("vdg_path"))

        for label, path in (
            ("outlier_item", outlier_path),
            ("comments", comments_path),
            ("vdg", vdg_path),
        ):
            if not path or not path.exists():
                issues.append(f"missing {label} file: {path}")

        if not issues:
            outlier_item = _load_json(outlier_path)
            comments = _load_json(comments_path)
            vdg = _load_json(vdg_path)

            checks = entry.get("checks", {})
            required_vdg_keys = checks.get("required_vdg_keys", [])
            min_comment_count = checks.get("min_comment_count", 0)
            feature_ranges = checks.get("feature_ranges", {})

            issues.extend(_validate_outlier_item(outlier_item))
            issues.extend(_validate_comments(comments, min_comment_count))
            issues.extend(_validate_vdg(vdg, required_vdg_keys, feature_ranges))

        if issues:
            failed += 1
            print(f"[FAIL] {entry_id}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[PASS] {entry_id}")

    print(f"\nSummary: total={total}, skipped={skipped}, failed={failed}")
    if args.fail_on_issue and failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
