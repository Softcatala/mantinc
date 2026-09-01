#!/bin/bash
# Autonomous driver: runs the 2 cloud + 18 local evals sequentially,
# regenerates the README results table from evals/*.json after each,
# commits the update, and pushes it to origin/harder. Only results created by
# this invocation are included, so stale evaluations cannot leak into README.
#
# Progress and per-model output goes to outputs/eval_driver.log.

set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"

LOG="$ROOT/outputs/eval_driver.log"
STATE="$ROOT/outputs/eval_driver.state"
mkdir -p "$ROOT/outputs"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "=== eval driver started (PID $$) ==="
RUN_STARTED_AT="${RUN_STARTED_AT_OVERRIDE:-$(date -Iseconds)}"

# Cache the export once up front. Every eval-target below is invoked with
# SKIP_EXPORT=1 so we don't re-export the JSONL 20 times.
log "exporting lm-eval jsonl"
if ! uv run make export-lm-eval >>"$LOG" 2>&1; then
  log "!!! export failed — aborting"
  exit 1
fi

CLOUD=(
  "eval-gpt56 gpt-5.6"
  "eval-gemini-flash-37 gemini-3.7-flash"
)

LOCAL_MODELS=(
  google_gemma-4-E4B-it-Q4_K_M
  google_gemma-3-4b-it-Q4_K_M
  aya-expanse-8b-Q4_K_M
  Meta-Llama-3.1-8B-Instruct-Q4_K_M
  EuroLLM-9B-Instruct-Q4_K_M
  Qwen_Qwen3.5-9B-Q4_K_M
  Ministral-3-8B-Instruct-2512-Q4_K_M
  salamandra-7b-instruct-2606.Q4_K_M
  google_gemma-3-12b-it-Q4_K_M
  gemma-4-12b-it-Q4_K_M
  Qwen_Qwen3-14B-Q4_K_M
  Ministral-3-14B-Instruct-2512-Q4_K_M
  phi-4-Q4_K_M
  mistralai_Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M
  google_gemma-3-27b-it-Q4_K_M
  google_gemma-4-26B-A4B-it-Q4_K_M
  Qwen3.8-27B-UD-Q4_K_M
  Muse-Glimmer-30B-UD-Q4_K_XL
)

post_eval() {
  local slug="$1"; local label="$2"
  log "regenerating README table"
  if ! uv run python - "$ROOT" "$RUN_STARTED_AT" >>"$LOG" 2>&1 <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
cutoff = sys.argv[2]
evals = root / "evals"
readme = root / "README.md"

display_names = {
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

rows = []
for path in sorted(evals.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    if str(data.get("created_at", "")) < cutoff:
        continue
    rows.append((path.stem, data))
rows.sort(key=lambda item: -float(item[1].get("pass_rate", 0.0)))

header = "| Model | Overall | Catalan token ratio | Monolingual | Cross basic | Multi-turn | Cross advanced | RAG context |"
lines = [header, "|---|---:|---:|---:|---:|---:|---:|---:|"]
top = float(rows[0][1].get("pass_rate", 0.0)) if rows else None

def pct(value: float) -> str:
    return f"{value * 100:.1f}%"

for slug, data in rows:
    cats = data.get("categories", {})
    rate = float(data.get("pass_rate", 0.0))
    overall = pct(rate)
    if rate == top:
        overall = f"**{overall}**"
    cat = lambda name: pct(float((cats.get(name) or {}).get("pass_rate", 0.0)))
    lines.append(
        f"| {display_names.get(slug, data.get('model', slug))} | {overall} | "
        f"{pct(float(data.get('catalan_token_ratio', 0.0)))} | "
        f"{cat('monolingual')} | {cat('crosslingual_basic')} | "
        f"{cat('multi_turn')} | {cat('crosslingual_advanced')} | "
        f"{cat('rag_context')} |"
    )

marker = "## Completed evaluations\n"
prefix, found, _ = readme.read_text(encoding="utf-8").partition(marker)
if not found:
    raise RuntimeError("could not locate completed-evaluations section")
section = (
    marker
    + "\nResults completed by the current 300-item evaluation run:\n\n"
    + "Prompt duplication is **0.0%** (0/300 entries) at the 0.8 similarity threshold.\n\n"
    + "\n".join(lines)
    + "\n"
)
readme.write_text(prefix + section, encoding="utf-8")
PY
  then
    log "!!! updater failed for $slug"
    return 1
  fi
  git add README.md scripts/run_all_evals.sh evals/ 2>>"$LOG"
  if git diff --cached --quiet; then
    log "no changes to commit for $slug"
    return 0
  fi
  if ! git commit -m "Refresh results table with $label eval" >>"$LOG" 2>&1; then
    log "!!! commit failed for $slug"
    return 1
  fi
  if ! git push origin harder >>"$LOG" 2>&1; then
    log "!!! push failed for $slug"
    return 1
  fi
  log "pushed $slug"
}

if [[ "${SKIP_CLOUD:-0}" != 1 ]]; then
  for entry in "${CLOUD[@]}"; do
    read -r target label <<<"$entry"
    log "--- starting cloud target=$target label=$label ---"
    echo "$label" > "$STATE"
    if uv run make "$target" SKIP_EXPORT=1 >>"$LOG" 2>&1; then
      log "cloud target=$target finished ok"
      post_eval "$label" "$label" || true
    else
      log "!!! cloud target=$target failed"
    fi
  done
fi

resume_ready=1
[[ -n "${RESUME_FROM:-}" ]] && resume_ready=0
for model in "${LOCAL_MODELS[@]}"; do
  if (( ! resume_ready )); then
    if [[ "$model" == "$RESUME_FROM" ]]; then
      resume_ready=1
    else
      log "skipping completed local model=$model"
      continue
    fi
  fi
  log "--- starting local model=$model ---"
  echo "$model" > "$STATE"
  if uv run make eval-local-openai SKIP_EXPORT=1 DISPLAY_MODEL="$model" LOCAL_NUM_CONCURRENT=2 GEN_KWARGS='{"temperature":0,"max_gen_toks":2048}' >>"$LOG" 2>&1; then
    log "local $model finished ok"
    post_eval "$model" "$model" || true
  else
    log "!!! local $model failed"
  fi
done

log "=== eval driver finished ==="
