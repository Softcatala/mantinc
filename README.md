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

# Example of case

Exemple de cas real (`cd_h20_177`):

**Usuari:** Hem d'ajudar un client que té problemes amb escàners de magatzem.

**Assistent:** La resposta ha de demanar proves concretes i proposar una solució
temporal segura.

**Usuari:** Their operator says scanner pairing, bluetooth drops, warehouse
labels, firmware version and offline mode.

**Assistent:** Tradueixo el fons tècnic a instruccions clares.

**Usuari:** Plantilla reusable (mixed headers):

ASUNTO / SUBJECT:

SITUACIÓN / SITUATION:

RIESGO / RISK:

ACCIÓN INMEDIATA / IMMEDIATE ACTION:

PRÓXIMO PASO / NEXT STEP:

**Assistent:** OK. I will do la revisión final antes de cerrar.

**Prompt final:** Fes la resposta.

Tots els casos del benchmark són als fitxers de prompts de [`data/`](data/).

## Benchmark Design

- The dataset is category-balanced: each category contains 60 items, so category
  scores remain directly comparable.
- Conversation cases do not use system prompts. The final user prompt is appended
  after the prior turns, so the benchmark tests whether the model follows the
  latest task while resisting cross-language priming.
- Explicit Catalan language instructions follow the app policy being tested:
  - unmodified `rag_context` items include a final Catalan instruction;
    hardened items deliberately remove that reset signal.
  - `monolingual` never includes an explicit Catalan instruction, because it
    models an ordinary Catalan conversation.
  - unmodified `crosslingual_basic`, `multi_turn`, and `crosslingual_advanced` include an
    explicit Catalan instruction only when the case contains non-Catalan text and
    the full final user prompt is shorter than 10 words.
- RAG documents come from CC BY 4.0 Diputació de Barcelona Open Data records,
  currently the paired `parcsequipaments_ca` and `parcsequipaments_es` datasets.
  Only safe descriptive fragments are kept; contact, location, schedule, and
  personal data fields are filtered out.

The dataset contains 300 items total (60 per category × 5 categories). It is
built deterministically with `make build`.

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
  `crosslingual_advanced`, or `rag_context`.
  - `monolingual`: Catalan-only prompts and context.
  - `crosslingual_basic`: A Catalan task with Spanish or English source
    material.
  - `multi_turn`: Conversations that test whether the model follows the
    language of the final request despite earlier crosslingual context.
  - `crosslingual_advanced`: Multi-turn conversations combining
    crosslingual body content, reusable-template or closing pressure, and
    assistant priming before the final Catalan ask.
  - `rag_context`: Retrieved-context prompts answered in Catalan.
    `rag_subtype` is `spanish_only` (30 items, 4 ES documents) or
    `bilingual_ca_es` (30 items: 20 with 3 ES + 1 CA and 10 with 2 ES + 2 CA).
- `harder_variant` (218 non-control items): adversarial pressure independent
  of `category`: `template_es`, `template_mixed`, or `short_implicit`.
- `rag_subtype` (only on `rag_context` items): `spanish_only` or
  `bilingual_ca_es`.
- `pressure_pattern`: consolidated classification of the
  language-drift pressure carried by the item, used for cross-category
  slicing:
  - `no_pressure` (60): monolingual items — control.
  - `english_or_trilingual` (7): unmodified English or trilingual pressure.
  - `rag_context` (13): retrieved context with the explicit Catalan guardrail.
  - `template_es_prior` (2): unmodified Spanish reusable-template pressure.
  - `harder_template_es` (61): saturated Spanish-template pressure.
  - `harder_template_mixed` (77): mixed ES/EN template pressure.
  - `harder_short_implicit` (80): dominant non-Catalan context followed by
    a short implicit Catalan task.
  Use `scripts/pressure_pattern_report.py` to slice model failures by
  pattern.
- `source_lang`: the source/context language pattern:
  - `ca`: Catalan-only prompt and context.
  - `es`: Spanish retrieved context answered in Catalan.
  - `ca-es`: mixed Catalan and Spanish retrieved context answered in Catalan.
  - `es-ca`: Spanish source material or prior-turn context answered in Catalan.
  - `en-ca`: English source material or prior-turn context answered in Catalan.
  - `en-es-ca` / `es-en-ca`: trilingual `crosslingual_advanced` items
    combining English and Spanish across prior turns (order marks the first
    crosslingual turn) answered in Catalan.

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

## Distributed adversarial pressure

Difficulty is independent of the scenario category. Three adversarial patterns
are distributed across all four non-control categories:

- `template_es` (61 items): Spanish reusable headers and Spanish assistant
  priming before the final Catalan task.
- `template_mixed` (77 items): combined ES/EN reusable headers and mixed
  assistant priming.
- `short_implicit` (80 items): dominant non-Catalan context followed by a
  short implicit Catalan task without an explicit language reset.

The other 22 non-control items retain their original pressure form where that
is needed to match the calibration target. No item asks for a Spanish or
English response; language failures therefore represent drift rather than
instruction following.

## Completed evaluations

Results on the 300-item dataset:

| Model | Overall | Catalan token ratio | Monolingual | Cross basic | Multi-turn | Cross advanced | RAG context |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.7 Flash | **94.0%** | 95.8% | 100.0% | 95.0% | 88.3% | 95.0% | 91.7% |
| Gemma 4 12B | 78.3% | 79.3% | 100.0% | 68.3% | 66.7% | 76.7% | 80.0% |
| Ministral 3 8B | 79.0% | 79.5% | 90.0% | 76.7% | 68.3% | 76.7% | 83.3% |
| Salamandra 7B Q4_K_M | 73.0% | 79.3% | 100.0% | 43.3% | 81.7% | 70.0% | 70.0% |
| Qwen3 14B | 75.3% | 81.8% | 100.0% | 61.7% | 76.7% | 78.3% | 60.0% |
| GPT-5.6 | 60.0% | 69.5% | 100.0% | 51.7% | 43.3% | 51.7% | 53.3% |

The pooled calibration target across the five models is 79/300 failures
(26.3%). The redistributed categories are within five percentage points of
that target:

| Category | Failures | Failure rate | Difference |
|---|---:|---:|---:|
| Crosslingual basic | 88/300 | 29.3% | +3.0 pp |
| Multi-turn | 94/300 | 31.3% | +5.0 pp |
| Crosslingual advanced | 73/300 | 24.3% | -2.0 pp |
| RAG context | 79/300 | 26.3% | 0.0 pp |

The maximum 95% margin of error is 5.7 percentage points for each pooled
category rate (n=300), using the normal approximation for a binomial
proportion. Per-model behavior varies, which is why calibration uses the pooled
model suite rather than forcing one prompt mix to move opposing models in the
same direction. All completed evaluations had zero API or empty-response
failures. Local changed-item runs used greedy decoding with
`max_gen_toks=2048`; unchanged deterministic samples were reused.
