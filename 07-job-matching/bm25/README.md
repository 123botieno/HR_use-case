# BM25: lexical ranking baseline

## Where this fits

BM25 ranks candidates by overlap between JD terms and CV terms. It is a transparent retrieval baseline: it measures lexical relevance, not verified qualification or probability of hiring.

## How scoring works

The code tokenizes each CV in the vacancy's frozen candidate pool, calculates document frequency for each term, and scores each candidate against the unique terms in the JD. Robertson IDF gives rarer terms more weight. Term frequency increases a score with diminishing returns, and document length normalization reduces the advantage of longer CVs.

## Settings (hyperparameters)

| Setting | Current value | Effect and tuning question |
|---|---:|---|
| `k1` | 1.5 | Controls term-frequency saturation. Higher values let repeated terms keep adding more weight. Test a small predeclared range such as 0.8, 1.2, 1.5, 2.0 on development vacancies. |
| `b` | 0.75 | Controls document-length normalization: 0 disables it; 1 applies full normalization by average CV length. Test a small range and inspect whether CV length is harming qualified candidates. |
| Query terms | Unique | Repeated terms in a JD count once. This avoids accidental emphasis from duplicated JD text. |
| Stop words | None | Common words remain. Test a documented language-aware list only if the same policy is applied consistently. |
| Tokenizer | Shared `TOKEN_PATTERN` | Determines what counts as a term; language, punctuation, and morphology affect matching. Version it when changed. |

The runner currently fixes `k1` and `b`; it does not perform a hyperparameter sweep. `bm25()` accepts explicit values for direct experiments, but command-line configuration is not yet exposed.

## Code walkthrough

1. The `score.py` entry point dispatches to the shared runner with `--methods bm25`.
2. `execute()` loads the prepared dataset, runs `validate_dataset()`, selects requested vacancies, and freezes a sorted candidate pool for each one.
3. The runner calls `bm25(query, documents)`. It tokenizes all CVs, counts term frequencies and document frequencies, and calculates average document length.
4. For each CV, it loops over unique JD tokens found in that CV, computes Robertson IDF and the BM25 term-frequency/length-normalization contribution, sums contributions into a score, and retains the strongest matched terms as evidence.
5. `rank()` pairs each score and evidence list with a candidate ID, sorts descending by score with candidate ID as the tie-break, assigns ranks/top-five flags, and marks cutoff ties or all-zero rankings.
6. `validate_rankings()` checks that the output still covers exactly the candidate pool and that ranks, scores, ordering, and shortlist flags are consistent.
7. The runner writes each result into `run.json`; after all vacancies/methods, it also writes `rankings.csv`, `shortlists.csv`, `comparison_shortlists.csv`, `judgments_template.csv`, `comparison.json`, and `report.md`.

Scoring exceptions are caught per JD-method pair and recorded in `run.json` under `failures`. The ranking is not partially emitted for a failed method.

## How to test a setting

Use development JDs with independently reviewed suitability labels. For each candidate setting, score the same frozen pool, then compare Recall@5, Precision@5, and NDCG@5 only when labels support those metrics. Choose settings on development JDs, freeze them, and evaluate once on held-out JDs. Do not choose `k1` or `b` based on held-out results.

## Run and inspect

```powershell
python 07-job-matching/bm25/score.py --jd JD-01
```

The command produces full rankings and a top-five shortlist through the shared runner. Ranking rows retain raw BM25 scores and up to 20 matched-term contributions. All-zero scores mark an uninformative ranking; cutoff ties are flagged.

## What discrepancy can it surface?

If a CV ranks highly because it repeats a rare term, inspect its term contributions and verify the actual evidence. If longer CVs systematically rank better or worse, examine the effect of `b` on development vacancies. Lexical matching cannot establish whether experience is current, equivalent, or sufficient.

## Discussion points

- Does repeated mention signal stronger evidence, or just document verbosity?
- Should rare technical terms receive more weight in this occupation?
- Which local language variants and transliterations should the tokenizer recognize?
- How will query-term duplicates and stop words be handled consistently?
- Is the method useful where the JD uses different wording from candidates' CVs?

## Limits

The implementation has no stemming, synonym expansion, semantic understanding, or evidence verification. Its scores are specific to this corpus and method and must not be compared numerically with TF-IDF or LLM scores.

## Related stages

See the [shared run contract](../README.md), [benchmark metrics](../comparison/README.md), and [MLflow experiment logging](../../03-mlflow/README.md).
