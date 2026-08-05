# Next step

Create a separate **hard split**. Keep the current 300 items as the baseline.

## Why

Top models are already near ceiling on many existing items, so broad rebalancing
will not improve discrimination enough.

## What to build

Add 100-150 harder but fair items that target observed top-model failures:

- Spanish/English template labels that must be translated.
- RAG metadata and source-language terms that must not be copied.
- Strong recency pressure before a Catalan final answer.
- Multi-turn Spanish/English assistant priming.
- Dense technical terms where loanwords are allowed but sentence framing stays Catalan.
- Mixed-language RAG snippets with duplicate or conflicting phrasing.
- Concise-output constraints to avoid truncation noise.

## How to select items

Run item analysis on the 9 existing model runs:

- Baseline-only: items passed by 9 / 9 models.
- Keep: items with roughly 30-80% pass rate.
- Extend: failure patterns from strong models.

## Acceptance criteria

- Hard split has 100-150 items.
- Prompt clarity pass rate is at least 95% in human review.
- Strong models show at least 20 percentage points of spread.
- Best model stays below roughly 85% on the first run.
- Report language drift, truncation, and task-completion separately.
