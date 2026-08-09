#!/usr/bin/env python3
"""Sample FLORES-200 sentences into the scorer validation slice."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lm_eval_tasks.catalan_drift.utils import _alpha_tokens

FLORES = ROOT / "data/flores200"
OUTPUT = ROOT / "data/language_validation.jsonl"
SEED = 42

LANGS = {
    "ca": ("cat_Latn", 100),
    "es": ("spa_Latn", 80),
    "en": ("eng_Latn", 40),
}

BUCKETS = [("short", 0, 10), ("medium", 10, 40), ("long", 40, 10_000)]


def bucket_of(n: int) -> str:
    for name, lo, hi in BUCKETS:
        if lo <= n < hi:
            return name
    raise ValueError(n)


def sample_lang(lang: str, code: str, target: int, rng: random.Random) -> list[dict]:
    sentences = []
    for split in ("dev", "devtest"):
        path = FLORES / split / f"{code}.{split}"
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            n = len(_alpha_tokens(line))
            if n == 0:
                continue
            sentences.append((bucket_of(n), n, line))
    by_bucket: dict[str, list[tuple[int, str]]] = {b[0]: [] for b in BUCKETS}
    for bucket, n, line in sentences:
        by_bucket[bucket].append((n, line))

    per_bucket = target // len(BUCKETS)
    remainder = target - per_bucket * len(BUCKETS)
    rows = []
    for i, (name, _, _) in enumerate(BUCKETS):
        want = per_bucket + (1 if i < remainder else 0)
        pool = by_bucket[name]
        if not pool:
            continue
        picks = rng.sample(pool, min(want, len(pool)))
        for n, text in picks:
            rows.append({"lang": lang, "shape": f"clean_sentence_{name}", "n": n, "text": text})
    return rows


def main() -> None:
    rng = random.Random(SEED)
    validation_slice = []

    for lang, (code, target) in LANGS.items():
        for row in sample_lang(lang, code, target, rng):
            validation_slice.append({
                "id": f"lv_flores_{lang}_{len(validation_slice):05d}",
                "source": "flores200",
                "shape": row["shape"],
                "segments": [{"lang": row["lang"], "text": row["text"], "alpha_tokens": row["n"]}],
            })

    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in validation_slice),
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUTPUT), "n": len(validation_slice)}))


if __name__ == "__main__":
    main()
