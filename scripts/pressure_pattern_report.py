#!/usr/bin/env python3
"""Per-pressure-pattern fail rates by model, over outputs/**/samples_*.jsonl.

Reads the consolidated `pressure_pattern` field baked into each dataset
item (see scripts/add_pressure_pattern.py).
"""

from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    "no_pressure",
    "english_or_trilingual",
    "inline_source_es",
    "midconv_es_recency",
    "rag_context",
    "template_es_prior",
    "harder_template_es",
    "harder_template_mixed",
    "harder_short_implicit",
]

items = {}
for path in sorted(ROOT.glob("data/prompts_*.yaml")):
    for r in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
        items[r["id"]] = r.get("pressure_pattern", "unknown")

results = defaultdict(dict)
for p in sorted(ROOT.glob("outputs/*/lm_eval/**/samples_*.jsonl")):
    model = p.relative_to(ROOT).parts[1].removesuffix("-harder")
    for line in open(p, encoding="utf-8"):
        s = json.loads(line)
        did = s.get("doc", {}).get("id")
        if did:
            results[model][did] = float(s.get("drift_pass", 0)) == 1.0

models = sorted(results)
agg = defaultdict(lambda: [0, 0])
totals = defaultdict(int)
for did, pat in items.items():
    totals[pat] += 1
    for m in models:
        if did in results[m]:
            agg[(pat, m)][0] += int(results[m][did])
            agg[(pat, m)][1] += 1


def short(m):
    for suf in ("-q4_k_m", "-instruct-2512"):
        m = m.replace(suf, "")
    return m.replace("qwen_qwen", "qwen").replace("gemma-4-", "gemma-").replace("gemini-3.7-", "gemini-")


rows = [["pattern", "n"] + [short(m) for m in models] + ["avg"]]
for pat in ORDER:
    if not totals.get(pat):
        continue
    row = [pat, str(totals[pat])]
    fails = []
    for m in models:
        k, n = agg[(pat, m)]
        if n:
            fails.append(100 * (n - k) / n)
            row.append(f"{fails[-1]:5.1f}%")
        else:
            row.append("    -")
    row.append(f"{sum(fails) / len(fails):5.1f}%" if fails else "    -")
    rows.append(row)

widths = [max(len(c) for c in col) for col in zip(*rows)]
for i, row in enumerate(rows):
    print("  ".join([row[0].ljust(widths[0])] + [row[j].rjust(widths[j]) for j in range(1, len(row))]))
    if i == 0:
        print("  ".join("─" * w for w in widths))

print()
print("Cells are % fail ratio: 100 × (items where the model drifted from Catalan) / n.")
