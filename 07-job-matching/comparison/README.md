# Comparing BM25, TF-IDF, and LLM rankings

## Purpose

Measure whether methods place independently judged suitable candidates near the top, under the same vacancy and candidate pool. Ranking agreement alone is not correctness.

## Evaluation flow

1. Define suitable and graded relevance with recruiters before looking at method outputs.
2. Keep reviewers blind to algorithm, score, and rank. Review candidates beyond the union of the three shortlists.
3. Use the generated full-pool `judgments_template.csv`; record suitable (0/1) and relevance (0..3), with 0 meaning unsuitable and 1..3 suitable.
4. Evaluate only metrics supported by the supplied labels. Unjudged candidates are not assumed unsuitable.
5. Tune model settings on development vacancies, freeze them, and report held-out results separately.

## Metrics

| Measure | Definition | Label requirement |
|---|---|---|
| Precision@5 | Suitable returned candidates divided by five | Every returned top-five candidate judged |
| Recall@5 | Suitable returned candidates divided by all suitable candidates in the pool | Complete pool judgments and at least one suitable candidate |
| NDCG@5 | Discounted graded relevance relative to ideal ordering | Complete pool judgments and nonzero ideal gain |
| Overlap | Shared top-five IDs and Jaccard similarity | Same candidate pool; does not require suitability labels |
| Runtime | Time spent scoring one vacancy-method pair | No recruiter labels |

For fewer than five returned candidates, missing positions count as zero for Precision@5 and returned count is reported. Incomplete pool labels make Recall@5 and NDCG@5 unavailable. The evaluator does not currently calculate confidence intervals, paired significance tests, or job-family aggregates.

## How the top five are selected, including ties

Each method returns a score for every candidate in the same vacancy pool. `shortlist.rank()` sorts by descending score, then ascending `candidate_id` for equal scores, and marks positions 1–5 as shortlisted. If ranks five and six have the same score, all candidates tied at that cutoff receive `cutoff_tie=true` in the full ranking. The output still contains exactly five candidates.

This tie rule is deterministic, but the candidate ID is only a reproducibility tie-break. It is not a qualification signal and does not mean the chosen candidate is better than another candidate with the same score. When the cutoff tie is flagged, treat the boundary as unresolved by the model and review tied candidates using job-related evidence or recruiter judgment. Changing the rule to include every cutoff tie would return more than five, so that policy would need to be agreed explicitly before use.

In the saved live run dated 15 October 2026 (`20261015T101453Z-402c9b11`), all 14 LLM vacancy rankings have a score tie between ranks five and six; each is flagged. Therefore, the fifth-place selection in each LLM list is determined by candidate ID among tied candidates. This is a limitation in how the top-five cutoff is operationalized, not a software sorting bug: the code follows its documented deterministic rule, but it cannot distinguish equal-scored candidates.

## Reading the three-method comparison

The project does not average BM25, TF-IDF, and LLM scores or combine their rankings. It compares three independent ranked lists for each JD:

1. **Overlap:** shared candidate count and Jaccard similarity show agreement between pairs of methods. Agreement does not show which method is correct.
2. **Judged quality:** Precision@5, Recall@5, and NDCG@5 use independent recruiter judgments only when their label coverage requirements are met.
3. **Operational measures:** runtime is recorded per JD-method. LLM token use and cache hits are recorded in the run; actual API billing is not available by default.
4. **Configuration and pool:** compare `pool_hash`, method configuration, and rubric status before attributing a difference to the algorithm.

Without independent judgments, the current evaluation cannot select a best-performing model. In that case, the comparison is exploratory: shortlist overlap and runtime can be reported, while suitability metrics remain unavailable.

## How the models are tested

The current runner uses fixed BM25 (`k1=1.5`, `b=0.75`) and TF-IDF (word unigrams, lowercase, L2 normalization) settings. It does not sweep hyperparameters. The LLM uses a fixed configured model and confirmed rubric. To test alternatives, use the same development JDs, pools, and judgments; change one predeclared configuration at a time; compare supported metrics; record each run and freeze settings before held-out evaluation. Never tune on held-out outcomes.

Raw scores are not comparable across methods. BM25 scores lexical term relevance, TF-IDF reports cosine similarity, and the LLM reports weighted supported-evidence coverage. Compare ranked outcomes and judgment metrics instead.

## Setup and use

Each matching run writes a blank full-pool judgment template. Have reviewers complete a copy without algorithm information, then run:

```powershell
python 07-job-matching/comparison/evaluate.py --run runs/RUN_ID/run.json --judgments data/judgments.csv
```

The evaluator writes `comparison.json` beside the run by default. It reports per-vacancy metrics and macro averages across evaluated vacancies. For exact behavior, see [evaluate.py](evaluate.py).

## Code walkthrough

1. The script forwards `--run` and optional `--judgments` through the shared CLI to `compare()`.
2. `judgments_from_csv()` reads labels, ignores blank rows, rejects duplicate JD/candidate IDs, parses the two integers, and enforces that relevance 0 means unsuitable while relevance 1–3 means suitable.
3. `compare()` rejects judgment keys absent from the run and calls `metrics()` for every JD-method ranking.
4. `metrics()` checks top-five label coverage for Precision@5 and full-pool label coverage for Recall@5 and NDCG@5. Unsupported values are returned as `None`.
5. For each vacancy, `compare()` confirms all methods used the same candidate pool, then calculates shared shortlist count and Jaccard overlap for every method pair.
6. It macro-averages each metric over vacancies where that metric is available and returns the full report object.
7. The CLI saves the report as `comparison.json` in the requested output path or beside `run.json` by default.

Invalid judgments or unequal pools raise `ValueError`; the evaluator does not guess missing labels or silently compare different candidate sets.

## Outputs and current data gaps

Each run folder contains:

| File | Contents and use |
|---|---|
| `run.json` | Full scores, ranks, evidence, configurations, pool hashes, runtime, validation results, and failures. Use it to investigate individual candidates and cutoff ties. |
| `rankings.csv` | All candidates, one row per JD and method, without long evidence payloads. |
| `shortlists.csv` | The five selected candidates per successful JD-method run, including cutoff tie flags. |
| `comparison_shortlists.csv` | Methods' top-five IDs and scores side by side for each vacancy. Scores are method-specific. |
| `report.md` | Human-readable top-five tables and failed method reasons. |
| `comparison.json` | Per-JD metrics, pairwise overlap, and macro averages. Quality metrics are null/unavailable until supported by labels. |
| `judgments_template.csv` | Full candidate pools with blank suitable/relevance labels for blind independent review. |

Current evidence gaps: no independent recruiter judgments are included; current source-derived rubrics are unconfirmed in the live LLM experiment; JD-13 and its 50 CVs are missing; CV-15-035 is unreadable; no confidence intervals or formal paired tests are computed; and overlap cannot establish correctness. The available 14-JD/699-CV live run is an experiment, not a validated hiring benchmark. Do not treat synthetic fit tiers or the Fairlearn teaching labels as recruiter judgments.

## What discrepancy does evaluation surface?

If BM25 has stronger overlap but lower judged Recall@5, it is retrieving similar lists without finding as many suitable candidates. If LLM results have high unknown-evidence shares, evidence availability may be limiting score interpretation. If methods perform differently across vacancies, inspect job family, pool size, rubric fit, and data quality before making an overall claim.

## Discussion points

- Does the relevance rubric reflect the vacancy's minimum requirements and priorities?
- Were candidates outside each shortlist judged so misses can be measured?
- Are all methods being compared on identical pools and held-out vacancies?
- Which error matters more operationally: missing a suitable candidate or returning an unsuitable one?
- How should uncertainty and disagreement between recruiters be represented?
- What evidence is sufficient to select a method for further piloting?

## Limits

No independent recruiter judgments are currently supplied by default, so suitability metrics can be unavailable. Synthetic judgments are useful for software demonstrations only. A metric cannot replace recruiter review, and a better benchmark score does not by itself establish lawful or fair use.

## Related stages

[Fairlearn](../../04-fairlearn/README.md) reports group selection rates and supported recall. Shared experiment tracking is covered in the workshop hub.
