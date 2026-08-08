# Com ajudar

Aquest conjunt de dades necessita revisió de casos reals: comprovar que els
prompts representen situacions versemblants, proposar casos nous i executar
l'avaluació amb altres models. Si vols col·laborar, deixa comentaris, idees o
resultats a [l'issue #1](https://github.com/jordimas/mantinc/issues/1).

# Introduction

Benchmark for checking whether a model keeps answering in Catalan across
monolingual, basic crosslingual, multi-turn, advanced crosslingual, and RAG
context prompts. The default harness runs the 300-item dataset. This targets the same
language-confusion problem studied by Marchisio et al. in
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
  `crosslingual_advanced`, or `rag_context`.
  - `monolingual`: Catalan-only prompts and context.
  - `crosslingual_basic`: A Catalan task with Spanish or English source
    material.
  - `multi_turn`: Conversations that test whether the model follows the
    language of the final request despite earlier crosslingual context.
  - `crosslingual_advanced`: Combined assistant priming/copying, momentum
    priming, and recency priming pressure cases.
  - `rag_context`: Retrieved-context prompts with Catalan and/or Spanish source
    snippets that must be answered in Catalan.
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
- When an example provides a template to use in another language, explicitly
  include `català` in the instruction. This keeps the case fair and makes the
  expected Catalan answer language unambiguous.
- RAG documents come from CC BY 4.0 Diputació de Barcelona Open Data records,
  currently the paired `parcsequipaments_ca` and `parcsequipaments_es` datasets.
  Only safe descriptive fragments are kept; contact, location, schedule, and
  personal data fields are filtered out.

The dataset contains 300 items total. It is built deterministically with
`make build`.

## Evaluation Results

| Model | Overall | Monolingual | Crosslingual basic | Multi-turn | Crosslingual advanced | RAG context |
|---|---:|---:|---:|---:|---:|---:|
| gemini-3.6-flash | **95.7%** | **100.0%** | **98.3%** | **96.7%** | **95.0%** | **88.3%** |

Scores are pass rates on the 300-item benchmark (60 items per category).


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
