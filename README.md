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

Install the dependencies for the model backend you intend to use:

```bash
# OpenAI-compatible APIs and LiteLLM providers
uv sync --extra api

# Local Hugging Face models
uv sync --extra local
```

The default installation contains only the common `lm-eval` dependency. The
`api` and `local` extras keep provider-specific dependencies optional. The
`dev` dependency group contains the test tooling and is installed by
`uv sync` by default; use `--no-dev` for a runtime-only environment.

Make targets select the `api` extra by default. Override `UV_EXTRAS` when
running another backend, for example:

```bash
make eval-one UV_EXTRAS=local LM_EVAL_MODEL=hf MODEL_ARGS='pretrained=your/model'
```

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
uv run --extra api lm_eval \
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

Input duplication is **0.0%** (0/300 entries) at Jaccard ≥ 0.8, measured over
the full model-visible input (conversation + retrieved context + prompt), not
the final prompt alone.

| Model | Overall | Catalan token ratio |
|---|---:|---:|
| GPT-5.6 | **71.3% ±5.1** | 76.2% |

`± N` is the Wilson 95% half-width at n=300. Rank differences smaller than
the two rows' combined half-widths are inside the CIs and should not be read
as capability gaps.

### Run configurations

Numbers above are conditioned on the decoding config each row was evaluated
under. They are not directly comparable across rows unless the configs match.

| Model | Provider | Precision | Temperature | Reasoning effort |
|---|---|---|---:|---|
| GPT-5.6 | OpenAI Chat Completions | fp16 | 0 | none |

### How to read this table

- **Not a capability ranking.** These numbers report drift performance under
  the specific decoding configs above, not raw model quality. A gap between
  rows may reflect decoding configuration or quantization, not the underlying
  model. Cloud and local rows may use different temperatures, reasoning settings,
  providers, and precision.
- **Sampling noise band.** Treat small rank differences as noise. Reported ranks
  are point estimates; no paired confidence intervals are computed yet.
- **What "Overall" measures.** Segment-level Catalan pass rate: each response
  is split into segments, each segment is classified by fastText, and the
  item passes iff the non-Catalan token ratio stays under 15%. Thresholds
  are calibrated against a FLORES-200 slice — see
  [`benchmark_design.md`](benchmark_design.md).

### Per-category diagnostic (do not rank)

These columns are meant to show *where* a model drifts, not to rank models
against each other. Each cell is one category with n=60, so the Wilson 95%
half-width sits in a ±3–12pp band depending on the pass rate. Treat any
per-cell difference smaller than the two cells' combined half-widths as
noise; the pattern within a row (which categories a model fails on) is the
signal to read.

| Model | Monolingual | Cross basic | Multi-turn | Cross advanced | RAG context |
|---|---:|---:|---:|---:|---:|
| GPT-5.6 | 100.0% ±3.0 | 78.3% ±10.2 | 60.0% ±12.0 | 60.0% ±12.0 | 58.3% ±12.1 |

For a finer diagnostic that cuts across categories, run
`python3 scripts/pressure_pattern_report.py` — it slices the same 300 items
by adversarial pressure pattern instead of scenario category.
