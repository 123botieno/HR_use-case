# Implementation and verification status

## Implemented

- The HR narrative centers on Fairlearn fairness evaluation and job-specific shortlist comparisons. Shared DVC, Great Expectations, MLflow, Evidently, and Prefect lessons are in the workshop hub.
- Core ranking supports BM25, TF-IDF, and a configurable OpenAI-compatible chat-completions LLM scorer.
- The Fairlearn case includes a fixed-seed fictional cohort, four separate group audits, paired saved results, a six-episode lab, facilitator notes, exercises, intro slides, and source notes.
- `requirements.lock` was resolved for Python 3.12 with the shared workshop MLOps versions. Use `uv venv --python 3.12 .venv` and `uv pip sync requirements.lock`.
- Raw CVs, prepared candidate data, virtual environments, MLflow stores/runs, and copied workshop repositories are excluded from the current Git tree. The root `downloads.json` contains SHA-256 hashes for the locally available CV bundle; use the USB restore script when needed.

## Earlier verification record

The previous implementation was tested on 15 October 2026 with Python 3.11.9. The hub's universal Python 3.12 lock is committed at the repository root. The saved Fairlearn reports use fictional data; no live OpenRouter request is needed for the fairness walkthrough.

## Data gaps and limits

- The original publisher, collection method, and license for the supplied CV/JD data were not recorded. Confirm authorization before using or sharing it.
- The raw source files and derived prepared applicant data are absent from Git; `python scripts/download.py --from <USB folder>` restores source files and checks their hashes.
- The original inventory contains absent files and an invalid DOCX, described in preparation outputs after restore.
- The Fairlearn demographic labels and suitability outcomes are fabricated. They cannot support claims about real applicants.
- Independent recruiter suitability judgments, a real audit collection policy, uncertainty analysis, and any approved disparity thresholds are not supplied.

See [RUNNING.md](RUNNING.md), [data source notes](../data/SOURCES.md), and the [Fairlearn workshop README](../04-fairlearn/README.md).
