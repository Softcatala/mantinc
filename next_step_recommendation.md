# Next-step recommendation

Your feeling is justified, but “the dataset is useless” is too harsh. My recommendation is: **stop expanding it, freeze it, and run one bounded validation sprint.** Don’t invest another open-ended month.

## What the evidence says

- **The easy problem is largely solved.** Strong models are near ceiling on monolingual and basic cross-lingual cases; the current results show GPT-5.6 at 100% there. Published work such as [LCB](https://aclanthology.org/2024.emnlp-main.380/) and [MuBench](https://aclanthology.org/2026.findings-acl.794/) supports the distinction between ordinary language adherence and harder mixed-language contexts.
- **The harder problem is not solved.** The advanced category scores only 21.7–50%, and RAG manual review found Spanish or English leakage such as `borrador`, `stakeholders`, and `fin de semana`.
- **The scorer is currently less reliable than the models.** Automatic RAG scoring said 10/10 clean, while provisional review found only 4/10 clean. Estimated recall was 17.6% for language ID and 33.3% for forbidden terms. Therefore, the nine-model table cannot yet prove either that the problem is solved or that models differ reliably.
- **The corpus itself is respectable.** It has 300 valid unique IDs, deterministic construction, and all 20 current tests pass. However, it also has 26 excess exact duplicates, 72 near-duplicate pairs, only 27 RAG source records, and 9/50 reviewed prompts lacking necessary facts.

## Value by intended use

| Intended use | Verdict |
|---|---|
| General multilingual research contribution | Limited novelty; LCB and IberoBench already cover the broad space |
| Reliable public model leaderboard | Not ready—the scorer invalidates rankings |
| Catalan adversarial regression suite | Potentially useful and fairly distinctive |
| Training dataset or general assistant-quality benchmark | Not suitable |

What you may be feeling is the collapse between “this will not become the contribution I imagined” and “the work has no value.” The first may be true; the second is not. You discovered that measurement—not necessarily model capability—is the bottleneck. That is a legitimate research result, although a disappointing one.

## Concrete stopping rule

1. Add no more prompts and evaluate no more models.
2. Have two Catalan speakers independently label the existing 50 responses, including the exact leakage spans.
3. Recalibrate the scorer.
4. Continue only if agreement reaches **κ ≥ 0.70**, precision **≥ 90%**, recall **≥ 85%**, and the advanced/RAG slices remain meaningfully below ceiling.

If that gate fails, publish or archive the work honestly as an experimental Catalan challenge set with a scorer-validity audit. That preserves the useful work without letting sunk cost claim another month.
