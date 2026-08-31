#!/bin/bash
# Autonomous driver: runs the 2 cloud + 18 local evals sequentially,
# regenerates the README results table from evals/*.json after each,
# commits the update, and pushes it to origin/harder.
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
  if ! uv run python "$ROOT/scripts/update_readme_results.py" >>"$LOG" 2>&1; then
    log "!!! updater failed for $slug"
    return 1
  fi
  git add README.md scripts/update_readme_results.py scripts/run_all_evals.sh evals/ 2>>"$LOG"
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

for model in "${LOCAL_MODELS[@]}"; do
  log "--- starting local model=$model ---"
  echo "$model" > "$STATE"
  if uv run make eval-local-openai SKIP_EXPORT=1 DISPLAY_MODEL="$model" LOCAL_NUM_CONCURRENT=2 >>"$LOG" 2>&1; then
    log "local $model finished ok"
    post_eval "$model" "$model" || true
  else
    log "!!! local $model failed"
  fi
done

log "=== eval driver finished ==="
