#!/usr/bin/env python3
"""Regenerate the README completed-evaluations table from evals/*.json.

Reads every `evals/<slug>.json` produced by `catalan_drift_eval.py
score-lm-eval` and rewrites the results table in README.md in place.
Highest overall pass rate is bolded.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
README = ROOT / "README.md"

# Map slug -> display name shown in the README table. Falls back to
# the JSON's `model` field when a slug is not listed here.
DISPLAY_NAMES = {
    "gpt-5.6": "GPT-5.6",
    "gemini-3.7-flash": "Gemini 3.7 Flash",
    "gemma-4-12b-it-q4_k_m": "Gemma 4 12B",
    "ministral-3-8b-instruct-2512-q4_k_m": "Ministral 3 8B",
    "ministral-3-14b-instruct-2512-q4_k_m": "Ministral 3 14B",
    "qwen_qwen3-14b-q4_k_m": "Qwen3 14B",
    "qwen_qwen3.5-9b-q4_k_m": "Qwen3.5 9B",
    "qwen3.8-27b-ud-q4_k_m": "Qwen3.8 27B",
    "salamandra-7b-instruct-2606.q4_k_m": "Salamandra 7B",
    "muse-glimmer-30b-ud-q4_k_xl": "Muse Glimmer 30B",
    "google_gemma-4-26b-a4b-it-q4_k_m": "Gemma 4 26B A4B",
    "google_gemma-3-27b-it-q4_k_m": "Gemma 3 27B",
    "google_gemma-3-12b-it-q4_k_m": "Gemma 3 12B",
    "google_gemma-3-4b-it-q4_k_m": "Gemma 3 4B",
    "google_gemma-4-e4b-it-q4_k_m": "Gemma 4 E4B",
    "mistralai_mistral-small-3.2-24b-instruct-2506-q4_k_m": "Mistral Small 3.2 24B",
    "meta-llama-3.1-8b-instruct-q4_k_m": "Llama 3.1 8B",
    "phi-4-q4_k_m": "Phi-4",
    "eurollm-9b-instruct-q4_k_m": "EuroLLM 9B",
    "aya-expanse-8b-q4_k_m": "Aya Expanse 8B",
}

HEADER = "| Model | Overall | Catalan token ratio | Monolingual | Cross basic | Multi-turn | Cross advanced | RAG context |"
SEP = "|---|---:|---:|---:|---:|---:|---:|---:|"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def load_evals() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(EVALS.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        slug = path.stem
        rows.append(
            {
                "slug": slug,
                "name": DISPLAY_NAMES.get(slug, data.get("model", slug)),
                "overall": float(data.get("pass_rate", 0.0)),
                "catalan_token_ratio": float(data.get("catalan_token_ratio", 0.0)),
                "categories": data.get("categories", {}),
            }
        )
    return rows


def row_line(row: dict, mark_best: bool) -> str:
    cats = row["categories"]
    def cat_rate(name: str) -> float:
        entry = cats.get(name) or {}
        return float(entry.get("pass_rate", 0.0))

    overall = pct(row["overall"])
    if mark_best:
        overall = f"**{overall}**"
    return (
        f"| {row['name']} | {overall} | {pct(row['catalan_token_ratio'])} | "
        f"{pct(cat_rate('monolingual'))} | {pct(cat_rate('crosslingual_basic'))} | "
        f"{pct(cat_rate('multi_turn'))} | {pct(cat_rate('crosslingual_advanced'))} | "
        f"{pct(cat_rate('rag_context'))} |"
    )


def build_table() -> str:
    rows = load_evals()
    if not rows:
        return HEADER + "\n" + SEP + "\n"
    rows.sort(key=lambda r: -r["overall"])
    top = rows[0]["overall"]
    lines = [HEADER, SEP]
    for row in rows:
        lines.append(row_line(row, mark_best=row["overall"] == top))
    return "\n".join(lines) + "\n"


def replace_table(text: str, table: str) -> str:
    pattern = re.compile(
        r"(^\| Model \| Overall .*\n\|---\|---:.*\n(?:\|.*\n)*)",
        re.MULTILINE,
    )
    if not pattern.search(text):
        raise RuntimeError("could not locate the results table in README.md")
    return pattern.sub(table, text, count=1)


def main() -> None:
    table = build_table()
    text = README.read_text(encoding="utf-8")
    README.write_text(replace_table(text, table), encoding="utf-8")


if __name__ == "__main__":
    main()
