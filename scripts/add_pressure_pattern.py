#!/usr/bin/env python3
"""Insert the consolidated `pressure_pattern` field into every dataset item.

Uses text-level insertion (a new line after each item's `target_lang: ca`)
so existing YAML formatting is preserved. Idempotent: skips items that
already carry the field.

Supported consolidated patterns (see README for definitions):
- no_pressure
- english_or_trilingual
- inline_source_es
- midconv_es_recency
- rag_context
- template_es_prior
- harder_template_es
- harder_template_mixed
- harder_short_implicit

Run: python scripts/add_pressure_pattern.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAMLS = [
    "data/prompts_monolingual.yaml",
    "data/prompts_crosslingual_basic.yaml",
    "data/prompts_multi_turn.yaml",
    "data/prompts_crosslingual_advanced.yaml",
    "data/prompts_rag_context.yaml",
]


def classify(r):
    cat = r.get("category", "")
    sl = r.get("source_lang", "")
    if cat == "monolingual":
        return "no_pressure"
    if r.get("harder_variant"):
        return f"harder_{r['harder_variant']}"
    if cat == "crosslingual_basic":
        return "inline_source_es" if sl == "es-ca" else "english_or_trilingual"
    if cat == "multi_turn":
        return "midconv_es_recency" if sl == "es-ca" else "english_or_trilingual"
    if cat == "rag_context":
        return "rag_context"
    if cat == "crosslingual_advanced":
        prior = " ".join(t.get("content", "") for t in r.get("conversation", []) if t.get("role") == "user")
        if "Plantilla reutilizable" in prior:
            return "template_es_prior"
        if "Reusable template" in prior:
            return "english_or_trilingual"
        if sl in ("en-es-ca", "es-en-ca"):
            return "english_or_trilingual"
        return "midconv_es_recency"
    return "unknown"


_ID_RE = re.compile(r"^- id: (\S+)")
_TARGET_LANG_RE = re.compile(r"^  target_lang: ca\s*$")
_PRESSURE_RE = re.compile(r"^  pressure_pattern:")


def label_file(path: Path) -> int:
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    labels = {r["id"]: classify(r) for r in rows}
    lines = path.read_text(encoding="utf-8").splitlines()

    out = []
    current_id = None
    inserted_ids: set[str] = set()
    already_present: set[str] = set()
    for line in lines:
        out.append(line)
        m = _ID_RE.match(line)
        if m:
            current_id = m.group(1)
            continue
        if current_id and _PRESSURE_RE.match(line):
            already_present.add(current_id)
            current_id = None
            continue
        if current_id and _TARGET_LANG_RE.match(line):
            out.append(f"  pressure_pattern: {labels[current_id]}")
            inserted_ids.add(current_id)
            current_id = None

    path.write_text("\n".join(out) + "\n" if not lines[-1] == "" else "\n".join(out), encoding="utf-8")
    return len(inserted_ids)


def main() -> None:
    for rel in YAMLS:
        path = ROOT / rel
        if not path.exists():
            print(f"skip (missing): {rel}")
            continue
        inserted = label_file(path)
        print(f"{rel}: inserted pressure_pattern into {inserted} items")


if __name__ == "__main__":
    main()
