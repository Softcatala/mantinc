#!/usr/bin/env python3
"""Utilities for the Catalan drift lm-eval task."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lm_eval_tasks.catalan_drift.utils import (
    CATALAN_FORBIDDEN_TERMS,
    forbidden_hits,
    process_results,
)


DEFAULT_PROMPTS = [
    "data/prompts_monolingual.yaml",
    "data/prompts_crosslingual_basic.yaml",
    "data/prompts_multi_turn.yaml",
    "data/prompts_crosslingual_advanced.yaml",
]


def _rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rows_from_paths(paths: list[str]) -> list[dict[str, Any]]:
    return [row for path in paths for row in _rows(Path(path))]


def _rows_with_dataset(paths: list[str]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        for source_row in _rows(Path(path)):
            row = dict(source_row)
            row["dataset_yaml"] = path
            rows.append(row)
    return rows


def _add_prompts_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompts", nargs="+", default=DEFAULT_PROMPTS)


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("response", "text", "content", "output"):
            text = _first_text(value.get(key))
            if text:
                return text
    if isinstance(value, (list, tuple)):
        for item in value:
            text = _first_text(item)
            if text:
                return text
    return ""


def _messages(row: dict[str, Any]) -> list[dict[str, str]] | None:
    if not row.get("conversation"):
        return None
    messages = [{"role": "system", "content": str(row["prompt"]).strip()}] + [
        {"role": str(turn["role"]), "content": str(turn["content"]).strip()}
        for turn in row["conversation"]
    ]
    normalized = [messages[0]]
    for message in messages[1:]:
        if normalized[-1]["role"] == message["role"]:
            normalized[-1]["content"] += "\n\n" + message["content"]
        else:
            normalized.append(message)
    messages = normalized
    if messages[-1]["role"] == "assistant":
        messages.append({"role": "user", "content": str(row["prompt"]).strip()})
    return messages


def _failure_details(sample: dict[str, Any], response: str) -> list[str]:
    doc = sample.get("doc", {})
    details = []
    if float(sample.get("api_or_empty_fail", 0)):
        details.append("api_or_empty_fail: empty response")

    if float(sample.get("forbidden_fail", 0)):
        forbidden_terms = [str(term) for term in (doc.get("forbidden_terms") or [])]
        if doc.get("target_lang") == "ca":
            forbidden_terms.extend(CATALAN_FORBIDDEN_TERMS)
        hits = forbidden_hits(
            response,
            forbidden_terms,
        )
        details.append("forbidden_fail: " + (", ".join(hits) if hits else "detected"))

    if float(sample.get("language_fail", 0)):
        details.append("language_fail: non-Catalan response detected")

    return details or ["drift_pass=0"]


def _conversation_lines(doc: dict[str, Any]) -> list[str]:
    if doc.get("conversation"):
        return [
            "CONVERSATION:",
            *[
                f"{str(turn.get('role', '')).upper()}: {str(turn.get('content', ''))}"
                for turn in doc["conversation"]
            ],
            "",
        ]
    return []


def export_lm_eval(args: argparse.Namespace) -> None:
    rows = _rows_with_dataset(args.prompts)
    for row in rows:
        messages = _messages(row)
        if messages:
            row["messages"] = messages
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(json.dumps({"prompts": args.prompts, "output": str(output), "n": len(rows)}))


def score_lm_eval(args: argparse.Namespace) -> None:
    samples = _rows_from_paths(args.samples)
    responses_path = Path(args.responses_output)
    responses_path.parent.mkdir(parents=True, exist_ok=True)
    responses = []
    failures = []
    passes = []

    for sample in samples:
        doc = sample.get("doc", {})
        response = _first_text(sample.get("filtered_resps") or sample.get("resps"))
        response_row = {
            "id": doc.get("id", sample.get("doc_id")),
            "category": doc.get("category"),
            "model": args.model,
            "provider": args.provider,
            "prompt": doc.get("prompt", ""),
            "response": response,
        }
        responses.append(response_row)
        if float(sample.get("drift_pass", 0)) == 0.0:
            failures.append((sample, response_row))
        else:
            passes.append((sample, response_row))

    responses_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in responses),
        encoding="utf-8",
    )

    api_or_empty_failures = [
        sample for sample, _ in failures if float(sample.get("api_or_empty_fail", 0))
    ]
    content_failures = [
        sample for sample, _ in failures if not float(sample.get("api_or_empty_fail", 0))
    ]
    content_samples = [
        sample for sample in samples if not float(sample.get("api_or_empty_fail", 0))
    ]
    report = {
        "content_pass_rate": (
            round((len(content_samples) - len(content_failures)) / len(content_samples), 4)
            if content_samples
            else 0.0
        ),
        "model": args.model,
        "n": len(samples),
        "n_api_or_empty_failures": len(api_or_empty_failures),
        "n_content_failures": len(content_failures),
        "n_content_samples": len(content_samples),
        "n_failures": len(failures),
        "n_passes": len(passes),
        "n_language_failures": sum(1 for sample, _ in failures if float(sample.get("language_fail", 0))),
        "pass_rate": round((len(samples) - len(failures)) / len(samples), 4) if samples else 0.0,
    }
    Path(args.report).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    parts = [
        f"# Failures: {args.model}",
        f"source: {' '.join(args.samples)}",
        f"n_failures: {len(failures)}/{len(samples)}",
        f"n_api_or_empty_failures: {len(api_or_empty_failures)}/{len(samples)}",
        f"n_content_failures: {len(content_failures)}/{len(content_samples)}",
        "",
    ]
    for index, (sample, response_row) in enumerate(failures, 1):
        details = _failure_details(sample, str(response_row.get("response", "")))
        parts += [
            "=" * 80,
            f"FAIL {index}/{len(failures)}",
            f"ID: {response_row['id']}",
            f"CATEGORY: {response_row.get('category')}",
            "REASONS:",
            *[f"- {detail}" for detail in details],
            "",
            *_conversation_lines(sample.get("doc", {})),
            "PROMPT:",
            str(response_row.get("prompt", "")),
            "",
            "OUTPUT:",
            str(response_row.get("response", "")),
            "",
        ]
    Path(args.failures_file).write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")

    pass_parts = [
        f"# Passes: {args.model}",
        f"source: {' '.join(args.samples)}",
        f"n_passes: {len(passes)}/{len(samples)}",
        "",
    ]
    for index, (sample, response_row) in enumerate(passes, 1):
        pass_parts += [
            "=" * 80,
            f"PASS {index}/{len(passes)}",
            f"ID: {response_row['id']}",
            f"CATEGORY: {response_row.get('category')}",
            "RESULT:",
            "- drift_pass=1",
            "",
            *_conversation_lines(sample.get("doc", {})),
            "PROMPT:",
            str(response_row.get("prompt", "")),
            "",
            "OUTPUT:",
            str(response_row.get("response", "")),
            "",
        ]
    Path(args.passes_file).write_text("\n".join(pass_parts).rstrip() + "\n", encoding="utf-8")


def _duration(seconds: float | None, missing: str = "-") -> str:
    return missing if seconds is None else f"{seconds:.1f}s"


def _inference_seconds(samples_path: Path, task: str) -> float | None:
    timestamp = samples_path.stem.removeprefix(f"samples_{task}_")
    result_path = samples_path.with_name(f"results_{timestamp}.json")
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        return float(result["total_evaluation_time_seconds"])
    except (KeyError, OSError, TypeError, ValueError):
        return None


def _wall_seconds(timeline_path: Path, runs: list[str]) -> float | None:
    if not timeline_path.exists():
        return None

    requested = set(runs)
    events = []
    for line in timeline_path.read_text(encoding="utf-8").splitlines():
        run, _, event, timestamp, *_ = line.split("\t")
        if run in requested and event in {"start", "end", "failed"}:
            when = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
            events.append((event, when))

    starts = [when for event, when in events if event == "start"]
    ends = [when for event, when in events if event != "start"]
    return max(ends) - min(starts) if starts and ends else None


def summary_lm_eval(args: argparse.Namespace) -> None:
    category_table = [["Task", "Model", "Pass", "Fail", "API empty", "Pass rate", "Fail rate", "Content pass", "Inference"]]
    dataset_table = [["Dataset YAML", "Model", "Pass", "Fail", "API empty", "Pass rate", "Fail rate", "Content pass", "Inference"]]

    def add_group_rows(table: list[list[str]], grouped: dict[str, list[dict[str, Any]]], run: str, inference: str) -> None:
        for group, rows in grouped.items():
            total = len(rows)
            passed = sum(float(row.get("drift_pass", 0)) == 1.0 for row in rows)
            failed = total - passed
            api_empty = sum(float(row.get("api_or_empty_fail", 0)) == 1.0 for row in rows)
            content_total = total - api_empty
            content_passed = sum(
                float(row.get("drift_pass", 0)) == 1.0
                for row in rows
                if not float(row.get("api_or_empty_fail", 0))
            )
            table.append([
                group, run, f"{passed}/{total}", f"{failed}/{total}",
                f"{api_empty}/{total}", f"{passed / total:.1%}",
                f"{failed / total:.1%}",
                f"{content_passed / content_total:.1%}" if content_total else "-",
                inference,
            ])

    for run in args.runs:
        paths = sorted((Path(args.outputs_dir) / run).glob(f"**/samples_{args.task}*.jsonl"))
        if not paths:
            raise FileNotFoundError(f"No samples found for {run}")
        samples_path = paths[-1]
        samples = _rows(samples_path)
        inference = _duration(_inference_seconds(samples_path, args.task))
        grouped: dict[str, list[dict[str, Any]]] = {"all": samples}
        by_dataset: dict[str, list[dict[str, Any]]] = {}
        for sample in samples:
            doc = sample.get("doc", {})
            category = str(doc.get("category") or "unknown")
            grouped.setdefault(category, []).append(sample)
            dataset = str(doc.get("dataset_yaml") or "unknown")
            by_dataset.setdefault(dataset, []).append(sample)
        add_group_rows(category_table, grouped, run, inference)
        add_group_rows(dataset_table, by_dataset, run, inference)

    def print_table(title: str, table: list[list[str]]) -> None:
        table[1:] = sorted(table[1:])
        widths = [max(len(row[index]) for row in table) for index in range(len(table[0]))]
        print(f"\n{title}\n")
        for index, row in enumerate(table):
            print("  ".join(
                value.rjust(widths[column]) if column >= 2 else value.ljust(widths[column])
                for column, value in enumerate(row)
            ))
            if index == 0:
                print("  ".join("-" * width for width in widths))

    print_table(f"lm-eval summary: {args.task}", category_table)
    print_table("lm-eval summary by dataset YAML", dataset_table)
    print(f"\ntotal wall time: {_duration(_wall_seconds(Path(args.timeline), args.runs), 'unavailable')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export-lm-eval")
    _add_prompts_arg(export_parser)
    export_parser.add_argument("--output", default="data/lm_eval/catalan_drift.jsonl")
    export_parser.set_defaults(func=export_lm_eval)

    score_parser = subparsers.add_parser("score-lm-eval")
    score_parser.add_argument("--samples", nargs="+", required=True)
    _add_prompts_arg(score_parser)
    score_parser.add_argument("--model", default="lm-eval")
    score_parser.add_argument("--provider", default="lm-eval")
    score_parser.add_argument("--responses-output", default="outputs/lm-eval.responses.jsonl")
    score_parser.add_argument("--report", default="outputs/lm-eval.report.json")
    score_parser.add_argument("--failures-file", default="outputs/failures_lm-eval.txt")
    score_parser.add_argument("--passes-file", default="outputs/pass_lm-eval.txt")
    score_parser.add_argument("--prompt-result-file", default=None)
    score_parser.set_defaults(func=score_lm_eval)

    summary_parser = subparsers.add_parser("summary-lm-eval")
    summary_parser.add_argument("--task", default="catalan_drift")
    summary_parser.add_argument("--outputs-dir", default="outputs/lm_eval")
    summary_parser.add_argument("--timeline", default="outputs/eval_timeline.tsv")
    summary_parser.add_argument("--runs", nargs="+", required=True)
    summary_parser.set_defaults(func=summary_lm_eval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
