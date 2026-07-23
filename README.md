# Com ajudar

Aquest conjunt de dades necessita revisió de casos reals: comprovar que els
prompts representen situacions versemblants, proposar casos nous i executar
l'avaluació amb altres models. Si vols col·laborar, deixa comentaris, idees o
resultats a [l'issue #1](https://github.com/jordimas/mantinc/issues/1).

# Introduction

Benchmark for checking whether a model keeps answering in Catalan across
monolingual, basic crosslingual, multi-turn, and advanced crosslingual prompts.
The default harness runs the 120-item dataset. This targets the same
language-confusion problem studied by Marchisio et al. in
["Understanding and Mitigating Language Confusion in LLMs"](https://aclanthology.org/2024.emnlp-main.380/)
as a foundation, while adding Catalan-specific personas, workflows, and
multi-turn pressure cases.

# Example of case

Exemple de cas real (`cd_h20_177`):

**Usuari:** Hem d'ajudar un client que té una integració amb errors intermitents
i dades que no quadren.

**Assistent:** La resposta ha de demanar proves concretes i proposar una solució
temporal segura.

**Usuari:** Their developer says webhook retry, payload mismatch, sandbox
account, production token and rate limit.

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
  `privacy_guidance`, `procurement_note`, `project_status`, `public_notice`,
  `public_project_status`, `study_plan`, `support_reply`, or `tenant_request`.
- `category`: `monolingual`, `crosslingual_basic`, `multi_turn`, or
  `crosslingual_advanced`.
  - `monolingual`: Catalan-only prompts and context.
  - `crosslingual_basic`: A Catalan task with Spanish or English source
    material.
  - `multi_turn`: Conversations that test whether the model follows the
    language of the final request despite earlier crosslingual context.
  - `crosslingual_advanced`: Combined assistant priming/copying, momentum
    priming, and recency priming pressure cases.
- `source_lang`: `ca`, `es-ca`, or `en-ca`. 
- `forbidden_terms`: source-language words or phrases that should not appear
  in the final answer.

The dataset contains 30 items in each of its four categories (120 items total).
It is built deterministically with `make build`.


## Run

This benchmark is designed to run as an `lm-eval` task. The task definition is
in `lm_eval_tasks/catalan_drift/`, and the exported prompt set is read from
`data/lm_eval/catalan_drift.jsonl`. Run `make export-lm-eval` before the command
below to build and export the dataset from a clean checkout.

Simple example:

```bash
uv run lm_eval \
  --include_path lm_eval_tasks \
  --tasks catalan_drift \
  --model openai-chat-completions \
  --model_args model=gpt-5.5 \
  --apply_chat_template \
  --log_samples \
  --output_path outputs/lm_eval/sample
```


## License

Code is licensed under the MIT License. Benchmark datasets, prompts, fixtures,
and source/evaluation data files are licensed under Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). See `LICENSE` for the
full repository license split.


## Completed evaluations

Results on the 120-item Catalan Drift dataset:

| Model | Overall | Monolingual | Crosslingual basic | Multi-turn | Crosslingual advanced |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-9B Q8 | **93.3%** | 100.0% | 100.0% | 96.7% | 76.7% |
| Gemma 4 E4B Q4 | 85.0% | 100.0% | 86.7% | 90.0% | 63.3% |
| Gemini 2.5 Flash | 83.3% | 100.0% | 100.0% | 93.3% | 40.0% |
| Gemma 3 12B Q8 | 82.5% | 96.7% | 100.0% | 93.3% | 40.0% |
| GPT-5.5 | 82.5% | 100.0% | 100.0% | 96.7% | 33.3% |
| Salamandra 7B Q8 | 80.0% | 100.0% | 83.3% | 86.7% | 50.0% |
| Ministral 3 8B Q8 | 75.8% | 93.3% | 83.3% | 86.7% | 40.0% |
| Qwen2.5 1.5B Q8 | 50.8% | 76.7% | 26.7% | 56.7% | 43.3% |
| Gemma 2 2B Q8 | 44.2% | 73.3% | 36.7% | 50.0% | 16.7% |

At 95% confidence, the maximum margin of error is ±8.9 percentage points
for overall scores (n=120) and ±17.9 percentage points for category scores
(n=30), using the normal approximation for a binomial proportion.

All completed evaluations had zero API or empty-response failures.
