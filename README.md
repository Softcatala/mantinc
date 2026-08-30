# Com ajudar

Aquest conjunt de dades necessita revisió de casos reals: comprovar que els
prompts representen situacions versemblants, proposar casos nous i executar
l'avaluació amb altres models. Si vols col·laborar, deixa comentaris, idees o
resultats a [l'issue #1](https://github.com/jordimas/mantinc/issues/1).

# Introduction

Benchmark for checking whether a model keeps answering in Catalan across
monolingual, basic crosslingual, multi-turn, advanced crosslingual, RAG
context, and harder-pressure prompts. The default harness runs the 360-item
dataset. This targets the same language-confusion problem studied by
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

# Example of case

Exemple de cas real (`cd_h20_177`):

**Usuari:** Hem d'ajudar un client que té problemes amb escàners de magatzem.

**Assistent:** La resposta ha de demanar proves concretes i proposar una solució
temporal segura.

**Usuari:** Their operator says scanner pairing, bluetooth drops, warehouse
labels, firmware version and offline mode.

**Assistent:** Tradueixo el fons tècnic a instruccions clares.

**Usuari:** Antes de terminar, incorpora los hechos, riesgos y próximos pasos
del contexto.

**Assistent:** D'acord. He revisat el context i en conservaré els elements clau.

**Usuari:** Haz una última revisión en español y deja lista la respuesta final.

**Assistent:** He revisado todo y tengo preparada una versión fiel, concreta y
completa.

**Prompt final:** Escriu la resposta de suport, amb comprovacions, dades
requerides, mesura temporal i escalat.

Tots els casos del benchmark són als fitxers de prompts de [`data/`](data/).

## Taxonomy

Each sample should specify:

- `persona`: `pime`, `administracio`, or `usuari_final`.
- `workflow`: one of the real task types used in the benchmark:
  `ai_misconception_explanation`, `citizen_response`, `client_delay_update`,
  `client_reply`, `community_health_bulletin`, `complaint_response`,
  `internal_briefing`, `privacy_guidance`, `procurement_note`,
  `project_status`, `public_info_summary`, `public_notice`,
  `public_project_status`, `service_summary`, `study_plan`, `support_reply`,
  or `tenant_request`.
- `category`: `monolingual`, `crosslingual_basic`, `multi_turn`,
  `crosslingual_advanced`, `rag_context`, or `harder`.
  - `monolingual`: Catalan-only prompts and context.
  - `crosslingual_basic`: A Catalan task with Spanish or English source
    material.
  - `multi_turn`: Conversations that test whether the model follows the
    language of the final request despite earlier crosslingual context.
  - `crosslingual_advanced`: Combined assistant priming/copying, momentum
    priming, and recency priming pressure cases.
  - `rag_context`: Retrieved-context prompts with Catalan and/or Spanish source
    snippets that must be answered in Catalan.
  - `harder`: Adversarial pressure patterns targeted at cracking language
    retention on models that saturate the other five categories. See the
    Harder category section below.
- `source_lang`: the source/context language pattern:
  - `ca`: Catalan-only prompt and context.
  - `es`: Spanish retrieved context answered in Catalan.
  - `ca-es`: mixed Catalan and Spanish retrieved context answered in Catalan.
  - `es-ca`: Spanish source material or prior-turn context answered in Catalan.
  - `en-ca`: English source material or prior-turn context answered in Catalan.

## Benchmark Design

- The dataset is category-balanced: each category contains 60 items, so category
  scores remain directly comparable.
- Conversation cases do not use system prompts. The final user prompt is appended
  after the prior turns, so the benchmark tests whether the model follows the
  latest task while resisting cross-language priming.
- Explicit Catalan language instructions follow the app policy being tested:
  - `rag_context` always includes a final Catalan instruction, because the app
    prompt supplies that guardrail around retrieved context.
  - `monolingual` never includes an explicit Catalan instruction, because it
    models an ordinary Catalan conversation.
  - `crosslingual_basic`, `multi_turn`, and `crosslingual_advanced` include an
    explicit Catalan instruction only when the case contains non-Catalan text and
    the full final user prompt is shorter than 10 words.
- RAG documents come from CC BY 4.0 Diputació de Barcelona Open Data records,
  currently the paired `parcsequipaments_ca` and `parcsequipaments_es` datasets.
  Only safe descriptive fragments are kept; contact, location, schedule, and
  personal data fields are filtered out.

The dataset contains 360 items total (60 per category × 6 categories). It is
built deterministically with `make build`.

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

### Scorer calibration

`LANGUAGE_MIN_CONFIDENCE` and `LANGUAGE_FAIL_NON_CA_RATIO` in
`lm_eval_tasks/catalan_drift/utils.py` are calibrated against one validation
slice: FLORES-200 dev+devtest sentences across `ca`, `es`, and `en`, bucketed
by length. Fetch the corpus with `make flores-corpus` and build the slice with
`scripts/build_slice.py`. The sweep measures per-language precision/recall
with Wilson 95% CIs computed over **segments** (one independent trial per
sentence), not tokens. Tokens within a segment share a prediction and are not
independent, so counting them shrinks CIs by roughly the mean segment length.

`scripts/compare_language_detectors.py` sweeps
`min_conf ∈ {0.30..0.90}` × `ratio ∈ {0.05..0.25}` over that slice and
writes `outputs/scorer_calibration.md` / `.json`. Only `min_conf` is
tuned: `ratio` is held at its current value because the slice is monolingual,
so gold ratio is 0 or 1 and does not provide a useful ratio signal. Surviving
candidates are ranked by segment F1 restricted to `ca`/`es`/`en`, the
languages actually gated on, and rounded to 3 decimals so the tie-break to
the current operating point can fire. CI acceptance uses the same 3-decimal
precision shown in the report, so `0/92` observed Catalan false positives
counts as a `0.040` Wilson upper bound and passes the 4% guard.

The recommended operating point is:

- `LANGUAGE_MIN_CONFIDENCE = 0.65`
- `LANGUAGE_FAIL_NON_CA_RATIO = 0.15`

If the sweep returns no recommended candidate, keep the current operating
point and grow the FLORES slice or revisit the acceptance criteria before
changing thresholds.

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

Results on the original 300-item Catalan Drift dataset (before the `harder`
category was added):

| Model | Overall | Catalan token ratio | Monolingual | Crosslingual basic | Multi-turn | Crosslingual advanced | RAG context |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma 4 12B Q4 | **99.7%** | 99.5% | 100.0% | 100.0% | 100.0% | 98.3% | 100.0% |
| Qwen3 14B Q4 | 99.3% | 99.1% | 100.0% | 100.0% | 100.0% | 98.3% | 98.3% |
| Gemini 3.7 Flash | 98.0% | 99.3% | 95.0% | 96.7% | 98.3% | 100.0% | 100.0% |
| GPT-5.6 | 96.0% | 95.9% | 100.0% | 100.0% | 96.7% | 83.3% | 100.0% |
| Ministral 3 8B Q4 | 94.3% | 91.8% | 90.0% | 86.7% | 98.3% | 98.3% | 98.3% |

At 95% confidence, the maximum margin of error is ±5.7 percentage points
for overall scores (n=300) and ±12.7 percentage points for category scores
(n=60), using the normal approximation for a binomial proportion.

**How to compare models:** Rank models by the **Overall** column. Per-category
scores (n=60, ±12.7 pp at 95%) are useful for spotting *where* a model
struggles, not for ranking models against each other — most per-category gaps
in this table are within the margin of error.

All completed evaluations had zero API or empty-response failures.

## Harder category

The original five categories saturate on strong models (top three between
98.0% and 99.7%, all within the ±5.7 pp margin of error). The `harder`
category adds 60 items built from three adversarial pressure patterns that
combine, in aggregate, into a benchmark that discriminates strong models
cleanly. Each item's `harder_variant` field identifies which pattern it uses:

- **`template_es`** (20 items): a Spanish reusable-template header block
  (`ASUNTO / SITUACIÓN / RIESGO / ACCIÓN INMEDIATA / PRÓXIMO PASO`) in a
  prior user turn, with a prior assistant already replying in Spanish. The
  final user turn asks the task in Catalan.
- **`template_mixed`** (20 items): the same template shape, but with mixed
  ES/EN section headers over trilingual body content in the prior turns.
- **`short_implicit`** (20 items): a long ES or EN source paragraph followed
  by a short (under ten words) Catalan task, with no explicit "en català"
  instruction.

None of these items contains an explicit "respond in Spanish/English"
directive — every item's final user turn is unambiguously Catalan. Failures
therefore represent genuine language drift, not instruction-following.

Results on the 60-item `harder` category:

| Model | Overall | template_es | template_mixed | short_implicit |
|---|---:|---:|---:|---:|
| Gemini 3.7 Flash | **95.0%** | 95.0% | 100.0% | 90.0% |
| Qwen3 14B Q4 | 88.3% | 90.0% | 90.0% | 85.0% |
| Gemma 4 12B Q4 | 78.3% | 100.0% | 100.0% | 35.0% |
| GPT-5.6 | 53.3% | 10.0% | 70.0% | 80.0% |
| Ministral 3 8B Q4 | 53.3% | 30.0% | 85.0% | 45.0% |

At 95% confidence, the maximum margin of error is ±12.7 pp for the 60-item
overall column and ±22 pp for the 20-item sub-pattern columns (normal
approximation). Even at those widths, the top-to-bottom spread of ~42 pp on
overall discriminates the five models cleanly.

Notable per-pattern findings:

- `template_es` cracks GPT-5.6 (10%) but the two open-weights 14B/12B models
  resist it (90%/100%). The Spanish-template trap is a GPT-5.6-specific
  weakness rather than a general language-confusion signal.
- `short_implicit` is where Gemma 4 12B collapses (35%), matching Ministral's
  weakness (45%) — long ES/EN source paragraphs with an implicit Catalan
  task line dominate its otherwise strong retention on the other categories.
- `template_mixed` is only really hard for GPT-5.6 (70%) and Ministral (85%);
  the other three models breeze through it.

All completed harder-category evaluations had zero API or empty-response
failures.
