# Dataset quality assessment task

Assess whether the Catalan Drift dataset is structurally valid, realistic, and scored fairly.

## Steps

1. Validate all 300 rows:
   - IDs are unique and required fields are present.
   - Each category contains 60 rows.
   - Conversations alternate roles and end with an assistant turn.
   - RAG chunks include source and licence information.

2. Review the annotations:
   - The dataset no longer carries per-row `forbidden_terms`; language drift is judged by
     the segment-level fastText detector in `lm_eval_tasks/catalan_drift/utils.py`
     (`lid.176.ftz`, non-Catalan token ratio ≥ 0.15 at confidence ≥ 0.71). Confirm the
     validator rejects any legacy `forbidden_terms`, `labels`, or `version` fields.
   - Valid Catalan words, names, trademarks, and accepted technical terms are not flagged
     by the detector as language drift (spot-check dense-terminology responses).
   - Duplicate and near-duplicate prompts are identified.

3. Review a balanced sample of 50 prompts, with 10 from each category. Check that each prompt is realistic, answerable, and clearly requests a Catalan response.

4. Run the same 50 prompts through one available model using temperature 0. Save the model version, settings, prompts, raw responses, errors, and finish reasons.

5. Score the responses automatically, then manually inspect every failure and at least two passes per category. Record:
   - Catalan language correctness.
   - Spanish or English leakage.
   - Task completion and truncation.
   - RAG grounding and unsupported claims.

6. Compare automatic and manual decisions. List false positives, false negatives, annotation problems, and coverage gaps.

## Scientific comparison

Compare the dataset and evaluation with Marchisio et al., [Understanding and Mitigating Language Confusion in LLMs](https://aclanthology.org/2024.emnlp-main.380/) (EMNLP 2024). Treat the paper as a reference methodology, not as a directly equivalent benchmark.

Assess and report:

- **Construct validity:** Is Catalan leakage clearly distinguished from acceptable names, technical terms, quotations, and natural code-switching? LCB explicitly separates language confusion from intentional code-switching.
- **Dataset evidence:** Compare this dataset's 300 Catalan examples and five task categories with LCB's 7,100 prompts, 15 languages, monolingual and cross-lingual settings, multiple data sources, human-written or human-edited data, and documented filtering. Note that this dataset has narrower external validity but adds targeted multi-turn, persona, workflow, and RAG cases absent from LCB.
- **Measurement validity:** Compare this benchmark's segment-level fastText detector (`lid.176.ftz`, 40-token windows, 15% non-Catalan token ratio at ≥ 0.71 confidence) with LCB's line-level fastText detector and word-level heuristics. Manually label a balanced subset, report scorer precision and recall, and double-annotate at least 20 failures or ambiguous cases. Report annotator agreement and resolve disagreements with a Catalan speaker.
- **Experimental reliability:** LCB evaluates several model families with a fixed 100-token limit and nucleus sampling (`p=0.75`, `temperature=0.3`), studies decoding and prompt-complexity effects, and repeats selected evaluations five times. Treat a single model at temperature 0 as a reproducible screening run, not evidence for model ranking or broad generalization. For stronger evidence, run all 300 examples on at least three model families and repeat stochastic runs at least three times.
- **Statistical reporting:** Give results by category with sample counts and 95% confidence intervals. Separate language leakage, instruction-following, truncation, and RAG-grounding errors instead of combining them into one score.
- **Reproducibility:** Record the dataset revision, model and tokenizer versions, prompt template, decoding settings, output limit, random seeds, raw outputs, scorer version, exclusions, and manual annotation decisions.

Rate construct validity, measurement validity, internal validity, external validity, reliability, and reproducibility as **strong**, **adequate**, or **weak**, with one sentence of evidence for each. The default conclusion should be that this is a focused exploratory benchmark and is less scientifically established than LCB unless the expanded inference, annotation-agreement, uncertainty, and reproducibility checks above are completed. Its multi-turn and RAG coverage may still make it more relevant for the specific Catalan use case.

## Commands

Any evaluation against local models must be run against `localhost:9090` (the local inference endpoint). Do not run local-model evals against any other host or port.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/assess_dataset_quality.py
.venv/bin/python scripts/run_inference_pilot.py --model gemma3:12b --per-category 10
```

## Deliverable

Write a self-contained HTML report at the repository root (`./report.html`) containing:

- Structural and annotation findings.
- Inference pass rates overall and by category, with 95% Wilson confidence intervals.
- Examples of scorer errors (false positives and false negatives, with the response text).
- Prompt, persona, workflow, and RAG coverage gaps.
- A comparison table against Marchisio et al. covering dataset scope, construct definition, metrics, controls, uncertainty, and reproducibility.
- A scientific-solidness rating with claims that the evidence does and does not support.
- A release decision: ready, ready with caveats, or needs revision.
- **A score card at the end** (see below).

Do not rank models unless inference errors are zero and the automatic scorer agrees closely with manual review.

### Score card

Render the score card as the final section of the HTML report. It is a table with one row per dimension and the columns: **Dimension**, **Score** (0–10), **Rating** (weak / adequate / strong), **Evidence** (one sentence with the concrete number), **Gaps** (what would raise the score). Average the per-dimension scores into a 0–10 headline (e.g., "6.3 / 10 — adequate"; that is the mean of the 13 dimension scores, equivalent to the sum divided by 13) and repeat the release decision.

Dimensions, grouped:

**Dataset**
1. **Structural integrity** — all 300 rows valid, IDs unique, 60 per category, conversations end on assistant turn, RAG chunks carry source and licence.
2. **Annotation quality** — absence of legacy `forbidden_terms`/`labels`/`version` fields (validator rejects them), exact- and near-duplicate rates, and fastText detector false-positive rate against a clean Catalan corpus.
3. **Coverage and balance** — persona × workflow × `source_lang` distribution across categories; call out thin cells.
4. **Prompt realism** — manual-review pass rate on the 50-prompt sample against the yes/no rubric (plausible scenario, answerable, final turn in Catalan or contains "català").

**Scorer**
5. **Language-ID accuracy** — fastText precision/recall on the manually labelled sample, with 95% Wilson CI.
6. **Detector false-positive rate on clean Catalan** — segment-level fastText false-positive rate per 10k tokens on a clean Catalan corpus (replaces the retired lexical forbidden-term check).
7. **Scorer–human agreement** — Cohen's κ on the drift_pass label across the manual sample; target κ ≥ 0.7.
8. **Scorer coverage** — which of {Catalan correctness, ES/EN leakage, task completion, truncation, RAG grounding} are automatic vs manual-only. Automatic ≥ 2 of 5 is adequate; ≥ 4 is strong.

**Evidence and reporting**
9. **Statistical reporting** — pass rates reported per category with sample counts and 95% CIs; error types kept separate rather than collapsed into one score.
10. **Experimental reliability** — number of model families evaluated and number of repeats for stochastic settings. Single model at T=0 is weak; ≥ 3 families and ≥ 3 repeats for at least one stochastic setting is strong.
11. **Construct validity** — Catalan leakage clearly separated from names, technical terms, quotations, and intentional code-switching.
12. **External validity** — how far results generalise beyond this 300-item, five-category, Catalan-only slice.
13. **Reproducibility** — dataset revision, model and tokenizer versions, prompt template, decoding settings, output limit, seeds, raw outputs, scorer version, exclusions, and manual annotation decisions all recorded and shipped with the report.

Rating scale per dimension (0–10): **0–3** weak, **4–6** adequate, **7–10** strong. A score of **0** means the evidence is absent or the check has not been run. A dimension may only score 7 or higher if the evidence sentence cites a concrete number (rate, CI, κ, count) — otherwise cap at 6.

### Dataset score card

A second, dataset-only score card, rendered right after the system score card. Same table shape (**Dimension**, **Score** 0–10, **Rating**, **Evidence**, **Gaps**) and same rule that a score of 7 or higher requires a concrete number. This one rates the 300-item corpus on its own merits, independent of the scorer and the inference pipeline.

Dimensions:

1. **Quality** — structural correctness, annotation accuracy, and duplicate rate. Evidence should cite: rows with missing/malformed fields, share of forbidden terms actually present in the source, exact- and near-duplicate counts, forbidden-list false-positive rate against a clean Catalan corpus.
2. **Usefulness** — how well the dataset targets the Catalan language-drift problem that the benchmark exists to measure. Evidence should cite: fraction of items where the final turn unambiguously requests Catalan, coverage of the drift-inducing conditions (crosslingual source, multi-turn priming, RAG mixing), and presence of Catalan-specific personas/workflows absent from LCB.
3. **Realism** — how plausible the scenarios are as real Catalan-speaking user tasks (SME, administration, end-user). Evidence should cite the manual-review pass rate on the 50-prompt sample against the "plausible scenario" criterion, plus any patterns of unrealistic prompts found.
4. **Difficulty and discriminative power** — whether the dataset separates stronger from weaker models rather than saturating or bottoming out. Evidence should cite the spread of overall pass rates across the 9 already-benchmarked models (README shows 40.3% to 85.0%) and per-category spread (crosslingual_advanced 23.3%–50.0% vs monolingual near-ceiling), and flag categories that are saturated or near-random.
5. **Maintainability and licensing** — determinism of `make build`, provenance and licence of source materials (RAG chunks from CC BY 4.0 Diputació de Barcelona; repository split MIT for code and CC BY-SA 4.0 for data), and ease of extending with new personas, workflows, or categories.

Close with a dataset headline on the same 0–10 scale (e.g., "6.4 / 10 — adequate"; that is the mean of the 5 dimension scores, equivalent to the sum divided by 5) and one sentence naming the single highest-leverage improvement to raise the lowest-scoring dimension.

## Action list, sorted by impact

Render this as the very last section of the HTML report, after both score cards. It is the "what to do next" ordered by how much the action would move the combined score card headlines, most impactful first. Each entry: **rank**, **action**, **primary dimensions it lifts** (link to the score-card rows), **effort** (S / M / L), **owner or blocker if known**, **acceptance criterion** (concrete, measurable). Keep to one line per action in the table; put any longer rationale in a footnote.

Baseline ordering (adjust after actually running the assessment; do not ship the report with this list unchanged):

1. **Manually label the 50-prompt sample and compute scorer precision, recall, and Cohen's κ.** Lifts: language-ID accuracy, forbidden-term precision/recall, scorer–human agreement. Effort: M. Acceptance: κ ≥ 0.7 and P ≥ 0.9, R ≥ 0.85 reported with 95% Wilson CI. *This gates the release decision — without it, most system-card dimensions are capped at 6.*
2. **Run the forbidden-term list against a clean Catalan corpus and log the false-positive rate.** Lifts: annotation quality, construct validity. Effort: S. Acceptance: false-positive rate < 1% per 10k Catalan tokens, with the offending terms listed for review.
3. **Split scorer coverage into automatic vs manual-only in the report and in `process_results` docstring.** Lifts: scorer coverage, construct validity. Effort: S. Acceptance: report contains an explicit coverage matrix over {Catalan correctness, ES/EN leakage, task completion, truncation, RAG grounding} and matches what the code actually computes.
4. **Reuse the existing 9-model 300-item runs as the primary evidence table; demote the 50-prompt pilot to scorer-audit only.** Lifts: experimental reliability, external validity, statistical reporting. Effort: S. Acceptance: report cites the 9-model table with per-category Wilson CIs and states pilot's role is scorer stability, not model ranking.
5. **Re-run the 50-prompt pilot on the smallest and largest already-benchmarked models at T=0 to test scorer stability across output styles.** Lifts: experimental reliability, scorer–human agreement. Effort: M. Acceptance: pass-rate delta between automatic and manual within ±5 pp for both models.
6. **Repeat at least one stochastic setting (LCB-style `p=0.75`, `temperature=0.3`) three times on one model to quantify run-to-run variance.** Lifts: experimental reliability, reproducibility. Effort: M. Acceptance: pass-rate standard deviation across 3 runs reported per category.
7. **Add the reproducibility manifest to the HTML report** (dataset revision hash, model + tokenizer versions, prompt template, decoding settings, output limit, seeds, scorer version, exclusions). Lifts: reproducibility. Effort: S. Acceptance: manifest section is present and each field is either filled or explicitly marked "n/a with reason".
8. **Rewrite step 3 as a three-item yes/no rubric** (plausible scenario, answerable, final turn in Catalan or contains "català") and record per-prompt scores. Lifts: prompt realism, construct validity. Effort: S. Acceptance: rubric spreadsheet shipped alongside the report; disagreement rate between two annotators reported.
9. **Double-annotate at least 20 failures or ambiguous cases and resolve disagreements with a Catalan speaker.** Lifts: measurement validity, scorer–human agreement. Effort: M. Acceptance: 20+ items with two independent labels, disagreements resolved and logged, Cohen's κ reported.
10. **Fill thin cells in the persona × workflow × `source_lang` matrix** flagged by the coverage report. Lifts: coverage and balance, external validity. Effort: L. Acceptance: no cell in the matrix under half the median cell count, without reducing category balance.
11. **Flag saturated and floored categories** (monolingual near-ceiling; crosslingual_advanced compressed near random) and either widen difficulty or note the ceiling/floor in the model-comparison table. Lifts: difficulty and discriminative power, external validity. Effort: M. Acceptance: each category's model spread is > 20 pp, or the report explicitly documents the ceiling/floor.
12. **Switch fastText from whole-response to line-level detection** to match LCB methodology, and A/B the two on the manual sample. Lifts: measurement validity, construct validity. Effort: M. Acceptance: line-level and whole-response scorer agreement reported; the higher-precision variant becomes the default.

Rules for maintaining the list:

- Re-sort after each score-card run. If completing the top action raises its dimensions to strong, drop it and let the next-highest-impact item take the top slot.
- An action stays on the list until its acceptance criterion is met and the corresponding score-card cell has been re-evaluated.
- Do not add items whose only justification is polish; every action must name at least one score-card dimension it moves.
