# 06 — Prefect: connect the stages into one run

## Where this fits

Prefect coordinates validation, scoring, evaluation, and optional tracking or monitoring. It makes task order and failures visible. In this project it is a callable local flow; it is not a deployed service or scheduled production pipeline.

## Current flow

1. Validate the prepared dataset with mandatory project checks and optional GX checks.
2. If `--version-repository` is supplied, call the DVC adapter on the dataset directory.
3. Run requested matching methods on the selected vacancy set.
4. Evaluate rankings against judgments if supplied; otherwise create a report with unavailable judgment metrics.
5. Optionally run the Fairlearn group audit when `--groups` is supplied.
6. Optionally monitor against a reference run when `--reference` is supplied.
7. Optionally track the run in MLflow when `--track-uri` is supplied.
8. Raise an error if the matching run is incomplete, while retaining its run artifacts and method failures.

The order is explicit in [pipeline.py](pipeline.py). Data preparation is separate. The flow does not automatically collect recruiter judgments or produce the synthetic Fairlearn teaching scenario.

## Setup and use

Install optional MLOps requirements. A BM25 and TF-IDF run with validation and MLflow tracking can be started with:

```powershell
python 06-prefect/pipeline.py --methods bm25 tfidf --gx --track-uri sqlite:///mlflow.db
```

For LLM matching, supply a confirmed rubric and API credentials. Optional `--reference`, `--groups`, `--judgments`, and `--version-repository` enable monitoring, group auditing, judgment evaluation, and DVC versioning. See [the running guide](../docs/RUNNING.md) for all arguments.

The flow may start Prefect's temporary local server. It does not configure a persistent server, deployment, schedule, notification, or remote worker.

## How failure appears

Dataset validation failures stop the flow before scoring. Matching method failures are recorded in `run.json`; successful method artifacts are retained. The flow then evaluates available results and ultimately raises if the run status is incomplete. Some optional post-run steps can fail independently and should be inspected in Prefect output and artifact files.

The scoring task uses zero Prefect retries. The LLM client's HTTP request has bounded retries for transient HTTP/network failures; that is internal to the client, not a retry of the entire matching task.

## Code walkthrough

1. The CLI parses flow options and dispatches to `prefect_run()` in [pipeline.py](pipeline.py).
2. `prefect_run()` sets a local Prefect home and imports `flow` and `task`, then resolves the other stage functions through `common.stages.stage()`.
3. It defines task wrappers: `validate` loads and checks data (and optionally GX); `matching` calls the shared `execute()` runner; `version` calls DVC; `evaluate` writes comparison JSON; `group_evaluation` runs Fairlearn; `monitoring` runs Evidently; `tracking` logs MLflow.
4. The `pipeline()` flow always runs validation first. It runs versioning only when a repository was given, then matching, then evaluation.
5. Group evaluation, monitoring, and tracking run only when their corresponding options are provided. These are conditional branches in Python, not automatically inferred from available files.
6. After optional artifacts are written, the flow checks matching status. An incomplete run raises `RuntimeError` that points to `run.json`; Prefect marks the flow failed while retaining the underlying run artifacts.
7. `prefect_run()` returns the flow result (the run directory on success). The script entry point passes command-line options through the shared CLI.

Prefect task return values make execution visible in its local UI/logs. The implementation does not declare task dependencies explicitly through futures; the flow's call sequence establishes the order. There is no whole-task retry, persistent deployment, or schedule.

## Discussion points

- Which stages need retries, and what would make a retry safe and idempotent?
- How can the flow preserve useful successful outputs when one method fails?
- What should trigger a human review before a run advances?
- What additional artifacts should each task return for observability?
- What changes are required before adding a deployment or schedule?

## Limits

This adapter demonstrates local orchestration. It does not provide durable production scheduling, access control, service-level objectives, alert routing, or a formal approval gate. Prefect coordinates configured checks; it cannot improve weak judgments or an unsuitable metric definition.

## Matching components

See [the three ranking methods and their settings](../07-job-matching/README.md).
