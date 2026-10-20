# 05 — Evidently: spot changes between ranking batches

## Where this fits

Monitoring compares a documented reference run with a later run. It can show that scores or document lengths shifted, or that top-five membership changed. It does not tell us that a model became less accurate unless independent suitability judgments are evaluated too.

## Flow

1. Choose a reference run with a known dataset, pool, and configuration.
2. Produce a later run for the same vacancies and methods.
3. For every current vacancy-method pair, find a matching reference pair.
4. Run Evidently’s `DataDriftPreset` on score and CV character-count columns.
5. Save per-pair HTML and JSON reports and an index with top-five Jaccard overlap, pool equality, and configuration equality.
6. Investigate shifts in context and, when judgments arrive, evaluate ranking quality separately.

## What the current monitor measures

The monitor segments by exact `(jd_id, algorithm)` pair because BM25, TF-IDF, and LLM score scales differ. It sends score and CV character count to Evidently. It computes shortlist overlap as the size of the intersection divided by the union of reference and current top-five IDs. The index reports whether pool hashes and configurations match. Missing reference pairs receive `no_reference` status.

It does not currently monitor language, extraction failures, missing evidence, group fairness, or recruiter-judged quality. It does not apply alert thresholds or automatically trigger remediation.

## Code walkthrough

1. The CLI dispatches `--reference`, `--current`, and `--output` to `monitor()` in [monitor.py](monitor.py).
2. `monitor()` loads both run JSON files and creates the output directory.
3. For each current result, it searches the reference results for the same JD and algorithm. If none exists, it records `no_reference` and skips the drift report for that pair.
4. For a match, an inner `frame()` extracts the candidate score and CV character count into pandas DataFrames. It creates Evidently's numerical `DataDefinition` and runs `DataDriftPreset` on the reference/current pair.
5. It saves an HTML report and JSON result named `<JD>-<algorithm>`.
6. It compares top-five candidate IDs to calculate Jaccard overlap and records pool-hash and configuration equality in the index row.
7. It saves all rows to `index.json` and returns them to the CLI.

The matching key prevents mixing score distributions between methods or vacancies. Evidently exceptions stop the command; there is no alert threshold or fallback statistic in the current adapter.

## Setup and use

Install the optional MLOps requirements and provide runs containing comparable vacancy-method pairs:

```powershell
python 05-evidently/monitor.py --reference runs/REFERENCE_ID/run.json --current runs/CURRENT_ID/run.json --output runs/monitoring
```

Inspect `index.json` first, then the corresponding HTML report. Comparing a run to itself checks report generation only; it does not measure repeatability across independent scoring calls.

## What discrepancy does monitoring surface?

A low top-five Jaccard value means the lists changed substantially. `same_pool=false` means the candidate set changed, so list movement may reflect pool composition. `same_config=false` means settings changed. A score-distribution drift result can reflect a real input or scoring change, but scores alone do not indicate whether suitability improved or worsened.

## Discussion points

- What reference period represents normal operations, and how often should it be refreshed?
- Should top-five overlap be measured only when pool and configuration match?
- Which score changes deserve investigation, and who should be notified?
- How could delayed recruiter outcomes be incorporated without confusing drift with performance?
- How will vacancies with no comparable reference be handled?

## Limits

Drift is a signal for investigation, not proof of model failure or bias. There are no project-specific thresholds, scheduled monitoring service, or alert routing. The feature set is currently limited to scores and document length.

## Next stage

[Prefect](../06-prefect/README.md) can coordinate a repeatable run and optional monitoring step.
