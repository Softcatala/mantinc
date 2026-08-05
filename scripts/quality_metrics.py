#!/usr/bin/env python3
"""For each of the 300 cases, list its most-similar neighbors by prompt Jaccard.

Also writes an offline HTML report to --html (default outputs/quality_metrics.html)
that shows every case side by side with its top neighbors.
"""

from __future__ import annotations

import argparse
import html
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_dataset import build_rows
from scripts.identify_duplicates import jaccard, normalize_text, token_set


def render_html(rows_by_id, neighbors_by_id, top, min_score) -> str:
    cases_with_duplicates = {
        row_id: neighbors
        for row_id, neighbors in neighbors_by_id.items()
        if neighbors
    }
    parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\"><head><meta charset=\"utf-8\">",
        "<title>Catalan Drift &mdash; per-case similarity</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#f4f5f7;color:#1b1b1b;}",
        "header{position:sticky;top:0;padding:12px 20px;background:#1c2b3a;color:#f4f5f7;z-index:5;}",
        "header h1{margin:0 0 4px;font-size:17px;}",
        "header .meta{font-size:12px;opacity:0.8;}",
        "main{padding:18px;display:grid;gap:14px;}",
        ".case{background:#fff;border:1px solid #d5d9df;border-radius:6px;padding:12px 16px;}",
        ".case h2{font-size:14px;margin:0 0 4px;}",
        ".case .meta{font-size:11px;color:#555;margin-bottom:6px;}",
        ".prompt{font-size:12px;background:#f8f9fb;border:1px solid #e2e5eb;border-radius:4px;padding:8px;white-space:pre-wrap;}",
        ".neighbors{margin-top:8px;display:grid;gap:6px;}",
        ".neighbor{display:grid;grid-template-columns:120px 60px 1fr;gap:8px;font-size:12px;padding:4px 6px;border-left:3px solid #274b72;background:#f6f8fb;}",
        ".neighbor .id{font-weight:600;color:#274b72;}",
        ".neighbor .score{color:#444;}",
        ".neighbor .snippet{white-space:pre-wrap;}",
        ".no-neighbors{font-size:12px;color:#888;font-style:italic;}",
        "</style></head><body>",
        "<header>",
        f"<h1>Duplicate cases &mdash; top {top} neighbors (Jaccard &ge; {min_score:.2f} on normalized prompt tokens)</h1>",
        f"<div class=\"meta\">"
        f"{len(cases_with_duplicates)} of {len(rows_by_id)} cases have at least one duplicate above threshold"
        "</div>",
        "</header><main>",
    ]

    if not cases_with_duplicates:
        parts.append("<p style=\"padding:20px;font-size:13px;\">No duplicates above threshold.</p>")

    for row_id, neighbors in cases_with_duplicates.items():
        row = rows_by_id[row_id]
        prompt = str(row.get("prompt") or "")
        parts.append("<section class=\"case\">")
        parts.append(f"<h2>{html.escape(row_id)}</h2>")
        parts.append(
            "<div class=\"meta\">"
            f"category={html.escape(str(row.get('category') or ''))} &middot; "
            f"persona={html.escape(str(row.get('persona') or ''))} &middot; "
            f"workflow={html.escape(str(row.get('workflow') or ''))} &middot; "
            f"{html.escape(str(row.get('source_lang') or ''))}&rarr;"
            f"{html.escape(str(row.get('target_lang') or ''))}"
            "</div>"
        )
        parts.append(f"<div class=\"prompt\">{html.escape(prompt)}</div>")
        parts.append("<div class=\"neighbors\">")
        for score, other_id in neighbors:
            other = rows_by_id[other_id]
            snippet = str(other.get("prompt") or "")
            parts.append(
                "<div class=\"neighbor\">"
                f"<span class=\"id\">{html.escape(other_id)}</span>"
                f"<span class=\"score\">{score:.3f}</span>"
                f"<span class=\"snippet\">{html.escape(snippet)}</span>"
                "</div>"
            )
        parts.append("</div></section>")

    parts.append("</main></body></html>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=3, help="Neighbors per row (default 3)")
    parser.add_argument("--min-score", type=float, default=0.8, help="Skip neighbors below this score (default 0.8)")
    parser.add_argument(
        "--html",
        type=Path,
        default=ROOT / "outputs" / "quality_metrics.html",
        help="Where to write the HTML report",
    )
    args = parser.parse_args()

    rows = build_rows()
    ids = [str(row["id"]) for row in rows]
    tokens = [token_set(normalize_text(str(row.get("prompt") or ""))) for row in rows]
    rows_by_id = {ids[i]: rows[i] for i in range(len(rows))}

    n = len(rows)
    similarity = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            score = jaccard(tokens[i], tokens[j])
            similarity[i][j] = score
            similarity[j][i] = score

    neighbors_by_id: dict[str, list[tuple[float, str]]] = {}
    for i, row_id in enumerate(ids):
        neighbors = sorted(
            ((similarity[i][j], ids[j]) for j in range(n) if j != i),
            key=lambda item: (-item[0], item[1]),
        )[: args.top]
        neighbors = [(s, nid) for s, nid in neighbors if s >= args.min_score]
        neighbors_by_id[row_id] = neighbors
        formatted = "  ".join(f"{nid}={s:.3f}" for s, nid in neighbors)
        if formatted:
            print(f"{row_id}  {formatted}")

    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(
        render_html(rows_by_id, neighbors_by_id, args.top, args.min_score),
        encoding="utf-8",
    )
    print(f"# HTML: {args.html}")

    with_duplicates = sum(1 for neighbors in neighbors_by_id.values() if neighbors)
    pct = (with_duplicates / n * 100) if n else 0.0
    print(f"# entries: {n}")
    print(f"# entries with duplication: {with_duplicates}")
    print(f"# duplication rate: {pct:.1f}%")

    for label, field in (("personas", "persona"), ("source languages", "source_lang")):
        counts = Counter(str(row.get(field) or "unknown") for row in rows)
        print(f"# {label}:")
        for value, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            share = (count / n * 100) if n else 0.0
            print(f"#   {value}: {count} ({share:.1f}%)")


if __name__ == "__main__":
    main()
