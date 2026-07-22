#!/usr/bin/env python3
"""Validate and summarize the deterministic Catalan Drift dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "monolingual": ROOT / "data/prompts_monolingual.yaml",
    "crosslingual_basic": ROOT / "data/prompts_crosslingual_basic.yaml",
    "multi_turn": ROOT / "data/prompts_multi_turn.yaml",
    "crosslingual_advanced": ROOT / "data/prompts_crosslingual_advanced.yaml",
}


def load_rows(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category, source in SOURCES.items():
        category_rows = load_rows(source)
        expected_source = str(source.relative_to(ROOT))
        if len(category_rows) != 30:
            raise ValueError(f"{source} must contain 30 rows, found {len(category_rows)}")
        for row in category_rows:
            if row.get("category") != category:
                raise ValueError(
                    f"{row.get('id')} in {source} has category {row.get('category')!r}"
                )
            if row.get("source_dataset_yaml") != expected_source:
                raise ValueError(
                    f"{row.get('id')} must reference {expected_source}"
                )
        rows.extend(category_rows)

    validate_rows(rows)
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> None:
    expected_categories = Counter({category: 30 for category in SOURCES})
    categories = Counter(str(row.get("category")) for row in rows)
    if len(rows) != 120 or categories != expected_categories:
        raise ValueError(f"unexpected category counts: {dict(categories)}")

    ids = [str(row.get("id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("dataset IDs must be unique")

    required = {
        "id",
        "category",
        "persona",
        "workflow",
        "source_lang",
        "target_lang",
        "prompt",
        "source_dataset_yaml",
    }
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"{row.get('id')} is missing fields: {sorted(missing)}")
        if row["target_lang"] != "ca":
            raise ValueError(f"{row['id']} must target Catalan")
        if "labels" in row or "version" in row:
            raise ValueError(f"{row['id']} contains internal or versioned metadata")
        conversation = row.get("conversation") or []
        if any(
            turn.get("role") not in {"user", "assistant"} or not turn.get("content")
            for turn in conversation
        ):
            raise ValueError(f"{row['id']} has an invalid conversation")


def distribution(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    values = [str(row.get(field) or "unknown") for row in rows]
    return dict(sorted(Counter(values).items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=ROOT / "data/prompts.distribution.json"
    )
    args = parser.parse_args()

    rows = build_rows()
    report = {
        "n": len(rows),
        "categories": distribution(rows, "category"),
        "overall": {
            field: distribution(rows, field)
            for field in ("source_lang", "persona", "workflow")
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"sources": list(map(str, SOURCES.values())), "report": str(args.report), "n": len(rows)}))


if __name__ == "__main__":
    main()
