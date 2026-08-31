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

Results on the 300-item dataset:

| Model | Overall | Catalan token ratio | Monolingual | Cross basic | Multi-turn | Cross advanced | RAG context |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.7 Flash | **88.7%** | 91.8% | 100.0% | 86.7% | 90.0% | 86.7% | 80.0% |
| Ministral 3 8B | 79.0% | 79.5% | 90.0% | 76.7% | 68.3% | 76.7% | 83.3% |
| Gemma 4 12B | 78.3% | 79.3% | 100.0% | 68.3% | 66.7% | 76.7% | 80.0% |
| Qwen3 14B | 75.3% | 81.8% | 100.0% | 61.7% | 76.7% | 78.3% | 60.0% |
| Llama 3.1 8B | 74.7% | 78.9% | 100.0% | 55.0% | 68.3% | 81.7% | 68.3% |
| Gemma 4 E4B | 73.7% | 81.0% | 98.3% | 46.7% | 71.7% | 80.0% | 71.7% |
| Salamandra 7B | 73.0% | 79.3% | 100.0% | 43.3% | 81.7% | 70.0% | 70.0% |
| Gemma 3 4B | 70.0% | 76.3% | 100.0% | 48.3% | 50.0% | 55.0% | 96.7% |
| GPT-5.6 | 68.0% | 72.6% | 100.0% | 66.7% | 50.0% | 61.7% | 61.7% |
| EuroLLM 9B | 61.0% | 69.7% | 100.0% | 61.7% | 28.3% | 43.3% | 71.7% |
| Aya Expanse 8B | 50.0% | 57.4% | 95.0% | 25.0% | 40.0% | 58.3% | 31.7% |

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
