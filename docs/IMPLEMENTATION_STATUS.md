# Implementation and verification status

## Implemented

- The numbered folders contain the DVC, Great Expectations, MLflow, Fairlearn, Evidently, Prefect, and matching implementations.
- Core ranking supports BM25, TF-IDF, and a configurable OpenAI-compatible chat-completions LLM scorer.
- The Fairlearn case includes a fixed-seed fictional cohort, four separate group audits, paired saved results, a six-episode lab, facilitator notes, exercises, intro slides, and source notes.
- `requirements.lock` was resolved for Python 3.12 with the shared workshop MLOps versions. Use `uv venv --python 3.12 .venv` and `uv pip sync requirements.lock`.
- Raw CVs, prepared candidate data, virtual environments, MLflow stores/runs, and copied workshop repositories are excluded from the current Git tree. The root `downloads.json` contains SHA-256 hashes for the locally available CV bundle; use the USB restore script when needed.

## Earlier verification record

The previous implementation was tested on 15 October 2026 with Python 3.11.9: the recorded core and MLOps integration tests passed, and a cached replay reproduced the then-current rankings. Those run files are local artifacts and are no longer committed. The new lock synced on Windows with Python 3.12.15; the test suite passed (30 passed, 1 skipped), and the Fairlearn gender audit ran from the committed synthetic inputs. No live OpenRouter request was made.

## Data gaps and limits

- The original publisher, collection method, and license for the supplied CV/JD data were not recorded. Confirm authorization before using or sharing it.
- The raw source files and derived prepared applicant data are absent from Git; `python scripts/download.py --from <USB folder>` restores source files and checks their hashes.
- The original inventory contains absent files and an invalid DOCX, described in preparation outputs after restore.
- The Fairlearn demographic labels and suitability outcomes are fabricated. They cannot support claims about real applicants.
- Independent recruiter suitability judgments, a real audit collection policy, uncertainty analysis, and any approved disparity thresholds are not supplied.

See [RUNNING.md](RUNNING.md), [data source notes](../data/SOURCES.md), and the [Fairlearn workshop README](../04-fairlearn/README.md).
