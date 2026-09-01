# Com ajudar

Aquest conjunt de dades necessita revisió de casos reals: comprovar que els
prompts representen situacions versemblants, proposar casos nous i executar
l'avaluació amb altres models. Si vols col·laborar, deixa comentaris, idees o
resultats a [l'issue #1](https://github.com/jordimas/mantinc/issues/1).

# Introduction

Benchmark for checking whether a model keeps answering in Catalan across
monolingual, basic crosslingual, multi-turn, advanced crosslingual, and RAG
context prompts. The default harness runs the 300-item dataset. This targets
the same language-confusion problem studied by
Marchisio et al. in
["Understanding and Mitigating Language Confusion in LLMs"](https://aclanthology.org/2024.emnlp-main.380/)
as a foundation, while adding Catalan-specific personas, workflows, and
multi-turn pressure cases.

## Scope

**What this benchmark measures:** whether the model's final answer is in
Catalan despite source-language pressure from prompts, prior turns, or retrieved
context. Scoring uses a fastText language check over response segments.

**What this benchmark does not measure:** task completion, factual accuracy,
tone, formatting, or overall answer quality. A model that refuses, goes
off-topic, or produces a poor answer *in fluent Catalan* will still pass. A
high score means "keeps the language," not "is a good Catalan assistant."

Design decisions, dataset taxonomy, and scorer calibration are documented in
[`benchmark_design.md`](benchmark_design.md).

# Example of case

Exemple de cas real (`cd_h20_177`):

**Usuari:** Hem d'ajudar un client que té problemes amb escàners de magatzem.

**Assistent:** La resposta ha de demanar proves concretes i proposar una solució
temporal segura.

**Usuari:** Their operator says scanner pairing, bluetooth drops, warehouse
labels, firmware version and offline mode.

**Assistent:** Tradueixo el fons tècnic a instruccions clares.

**Usuari:** Standard template (ES/EN):

DESTINATARIO / RECIPIENT:

MOTIVO / REASON:

ANTECEDENTES / BACKGROUND:

DECISIÓN / DECISION:

PLAZO / DEADLINE:

**Assistent:** OK. I will do la revisión final antes de cerrar.

**Prompt final:** Fes la resposta.

Tots els casos del benchmark són als fitxers de prompts de [`data/`](data/).


## Run

This benchmark is designed to run as an `lm-eval` task. The task definition is
in `lm_eval_tasks/catalan_drift/`, and the exported prompt set is read from
`data/lm_eval/catalan_drift.jsonl`. Run `make export-lm-eval` before the command
below to build and export the dataset from a clean checkout.

Language scoring uses the fastText command-line tool with the `lid.176` model.
This is intentionally not declared as a Python dependency: the available Python
packages are bindings, while this task shells out to the `fasttext` executable
with `predict-prob`. Install the OS package when available, put a built
`fasttext` executable on `PATH`, place it at `models/fasttext`, or set
`LANGUAGE_ID_FASTTEXT_BIN`.

```bash
sudo apt install fasttext
make language-id-model
```

`make language-id-model` downloads the default model to `models/lid.176.ftz`.
Set `LANGUAGE_ID_MODEL` to use another model path.

Simple example:

```bash
uv run lm_eval \
  --include_path lm_eval_tasks \
  --tasks catalan_drift \
  --model openai-chat-completions \
  --model_args model=gpt-5.6 \
  --apply_chat_template \
  --gen_kwargs '{"reasoning_effort":"none","temperature":0}' \
  --log_samples \
  --output_path outputs/lm_eval/sample
```

## License

Code is licensed under the MIT License. Benchmark datasets, prompts, fixtures,
and source/evaluation data files are licensed under Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). See `LICENSE` for the
full repository license split.

## Completed evaluations

Results from the current 300-item evaluation run.

Input duplication is **0.0%** (0/300 entries) at Jaccard ≥ 0.8 — and also 0/300 at
Jaccard ≥ 0.6 — measured over the full model-visible input (conversation +
retrieved context + prompt), not the final prompt alone.

| Model | Overall | Catalan token ratio | Monolingual | Cross basic | Multi-turn | Cross advanced | RAG context |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.7 Flash | **92.7%** | 95.5% | 100.0% | 95.0% | 91.7% | 98.3% | 78.3% |
| Ministral 3 8B | 80.0% | 80.5% | 91.7% | 80.0% | 61.7% | 75.0% | 91.7% |
| Gemma 3 4B | 75.7% | 80.8% | 100.0% | 50.0% | 66.7% | 61.7% | 100.0% |
| Llama 3.1 8B | 74.0% | 79.5% | 100.0% | 58.3% | 66.7% | 83.3% | 61.7% |
| Gemma 4 E4B | 73.0% | 82.4% | 98.3% | 53.3% | 68.3% | 76.7% | 68.3% |
| GPT-5.6 | 70.7% | 76.8% | 100.0% | 76.7% | 55.0% | 61.7% | 60.0% |
| EuroLLM 9B | 64.7% | 77.2% | 100.0% | 65.0% | 30.0% | 53.3% | 75.0% |
| Aya Expanse 8B | 48.3% | 56.1% | 95.0% | 31.7% | 40.0% | 43.3% | 31.7% |
| Qwen3.5 9B | 16.3% | 97.3% | 56.7% | 25.0% | 0.0% | 0.0% | 0.0% |

### Run configurations

Numbers above are conditioned on the decoding config each row was evaluated
under. They are not directly comparable across rows unless the configs match.

| Model | Provider | Precision | Temperature | Reasoning effort |
|---|---|---|---:|---|
| Gemini 3.7 Flash | LiteLLM (Google) | fp16 | 1.0 | low |
| GPT-5.6 | OpenAI Chat Completions | fp16 | 0 | none |
| Gemma 3 4B | local OpenAI-compatible | Q4_K_M | 0 | none (thinking disabled) |
| Gemma 4 E4B | local OpenAI-compatible | Q4_K_M | 0 | none (thinking disabled) |
| Llama 3.1 8B | local OpenAI-compatible | Q4_K_M | 0 | none |
| Ministral 3 8B | local OpenAI-compatible | Q4_K_M | 0 | none |
| EuroLLM 9B | local OpenAI-compatible | Q4_K_M | 0 | none |
| Aya Expanse 8B | local OpenAI-compatible | Q4_K_M | 0 | none |
| Qwen3.5 9B | local OpenAI-compatible | Q4_K_M | 0 | none |

### How to read this table

- **Not a capability ranking.** These numbers report drift performance under
  the specific decoding configs above, not raw model quality. A gap between
  two rows may reflect the config or the quantization, not the underlying
  model — Gemini samples at `temperature=1` with `reasoning_effort=low`,
  GPT-5.6 runs deterministically at `temperature=0` with reasoning off, and
  every local row uses Q4_K_M weights against a local OpenAI-compatible
  server.
- **Sampling noise band.** Five identical-config reruns of GPT-5.6 at
  `temperature=0` spread across 65–71% overall pass rate — a ~6pp band with
  nothing changed. Treat rank differences smaller than ~6pp as noise.
  Reported ranks are point estimates; no paired confidence intervals are
  computed yet.
- **Quantized decode collapse.** Local rows use Q4_K_M weights. Qwen3.5 9B
  shows why this matters: 97.3% of its emitted tokens are Catalan, yet its
  pass rate is 16.3% because the model produces truncated subword salad
  (e.g. `**Actualitzatedact`, `Benving arres`). The scorer counts those as
  `language_fail` correctly — they aren't Catalan — but the failure mode is
  decoding collapse under quantization, not language drift. Don't read this
  row as a comment on Qwen3.5's Catalan capability at full precision.
- **Scorer scope.** `language_fail` bundles genuine drift and any non-Catalan
  output the fastText `lid.176` detector recognizes, including garbled
  generation. The scorer does not currently distinguish drift from decode
  collapse; see the Qwen3.5 case above.
- **What "Overall" measures.** Segment-level Catalan pass rate: each response
  is split into segments, each segment is classified by fastText, and the
  item passes iff the non-Catalan token ratio stays under 15%. Thresholds
  are calibrated against a FLORES-200 slice — see
  [`benchmark_design.md`](benchmark_design.md).
