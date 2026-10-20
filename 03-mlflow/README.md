# 03 — MLflow: record what was run and compare what was judged

## Where this fits

MLflow stores experiment parameters, metrics, and selected artifacts so reviewers can relate an outcome to a dataset version and matching configuration. It does not train or promote a model in this project. The current matcher runs three separate ranking methods: BM25, TF-IDF, and an optional LLM evidence scorer.

## Flow

1. Run the methods on the same candidate pool for each vacancy.
2. Optionally fill the generated full-pool judgment template using independent recruiter review.
3. Run the comparison evaluator to calculate supported ranking metrics.
4. Track the run: one parent run records dataset/code/version metadata; nested runs record one vacancy-method result.
5. Inspect results by vacancy. Compare quality metrics only where judgments support them; compare runtime and LLM usage separately.

## What the current tracker logs

The parent logs dataset hash, project version, run status, Git revision when available, and code hash. Each nested JD-method run logs vacancy, method, pool hash, runtime, shortlist count, configuration JSON, and available Precision@5, Recall@5, and NDCG@5 from a neighboring `comparison.json`. LLM runs also record token counts and cache hits. Candidate text and evidence are not logged by default.

The tracker does not currently create a parent/child run per whole benchmark plus method across all vacancies, register fitted vectorizers, set promotion rules, or automatically version artifacts through DVC. Configurations are included as artifacts, but not every configuration field is a searchable MLflow parameter.

## Code walkthrough

1. The entry point dispatches `--run` and `--uri` to `track()` in [track.py](track.py).
2. `track()` loads `run.json` and checks for `comparison.json` beside it. If present, it loads those evaluation metrics; if absent, it continues without them.
3. It sets the MLflow tracking URI and experiment name, then opens one parent run named for the matching run ID.
4. The parent logs dataset hash, project version, status, Git revision (or `unversioned`), and code hash.
5. For every successful `results` entry, it opens a nested run named `<JD>-<algorithm>`, logs JD, algorithm, pool hash, runtime, and shortlist count.
6. If matching metrics exist in the comparison report, it logs Precision@5, Recall@5, and NDCG@5 only when non-null.
7. For LLM entries it sums uncached token usage and counts cache hits. It logs each method configuration as `configuration.json` and avoids candidate evidence/text.
8. If a comparison report was loaded, it logs that JSON artifact, closes the parent run, and returns the MLflow run ID.

MLflow errors are raised by the client and CLI; there is no fallback tracker in this adapter. Failed method records are in the run JSON but do not get nested MLflow runs because the tracker iterates successful results.

## Hyperparameters and experiment design

The current ranking settings are fixed, not automatically tuned:

| Method | Current settings recorded | What to vary on development vacancies |
|---|---|---|
| BM25 | `k1=1.5`, `b=0.75`, unique query terms, tokenizer pattern, no stop-word removal | `k1` controls term-frequency saturation; `b` controls document-length normalization. Test a small predeclared grid and tokenizer/stop-word choices. |
| TF-IDF | lowercase, word unigrams, L2 normalization, no stop-word removal, fitted vocabulary and IDF | Compare unigram/bigram ranges, stop-word policy, minimum document frequency, and normalization. Keep fitting within each frozen candidate pool. |
| LLM | model, endpoint, rubric hash, prompt version, provider, storage setting, rubric confirmation | Compare confirmed rubric weights or prompt versions only on development vacancies; record model and request settings. Current API payload uses strict JSON output and omits temperature. |

Tune only on development JDs, then freeze settings before held-out evaluation. Do not select settings using held-out recruiter judgments. The runner currently has no hyperparameter sweep or cross-validation; a reviewer can compare separately configured runs, but these settings must first be exposed as explicit options to vary them systematically.

## Setup and use

Track an existing run after creating the optional comparison report:

```powershell
python 07-job-matching/comparison/evaluate.py --run runs/RUN_ID/run.json --judgments data/judgments.csv
python 03-mlflow/track.py --run runs/RUN_ID/run.json --uri sqlite:///mlflow.db
```

If no judgment file is available, the comparison still reports supported non-label information elsewhere, but MLflow will not contain retrieval quality metrics. The tracker reads `comparison.json` beside `run.json` when it exists.

## What discrepancy does MLflow help explain?

If one method has lower Recall@5 on judged vacancies, inspect its configuration, pool hash, evidence, and failures. If quality is similar but runtime differs, the recorded runtime helps explain operational cost. Raw BM25, TF-IDF, and LLM scores have different meanings and scales: do not compare their magnitudes directly.

## Discussion points

- Are independent judgments complete enough to support Recall@5 and NDCG@5?
- Which metrics should be predeclared for a development/held-out comparison?
- How should runs with different candidate pools be handled?
- What additional settings and artifacts should become searchable parameters?
- Which artifacts may contain personal or sensitive information and should stay out of tracking?

## Limits

No independent recruiter judgments have been supplied by default, so quality metrics may be unavailable. Tracking a metric does not make it valid. There is no model registry promotion, automatic hyperparameter search, or fairness gate in this adapter.

## Next stage

[Fairlearn](../04-fairlearn/README.md) examines group differences when appropriate audit data exists; [Evidently](../05-evidently/README.md) compares batches over time.
