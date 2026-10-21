# Ethiopia Job Matching and Shortlisting

Compare an open-weight LLM, BM25, and TF-IDF on the same candidate pool for each job description (JD). Each method returns its own ranked shortlist of five candidates. Recruiters review suitability and evidence; a ranking score is not a probability of hiring or job success.

## Project status

Python implementations now cover document preparation, BM25, TF-IDF, OpenRouter-compatible LLM evidence scoring, top-five selection, judgment-based evaluation, and optional DVC, Great Expectations, MLflow, Fairlearn, Evidently, and Prefect integrations. Each stage folder contains its implementation and runnable command. Only file I/O, tokenization, and numbered-folder loading live in `common/`; `jobmatch/` contains the shared CLI dispatcher.

See [the running guide](docs/RUNNING.md) for setup and commands. BM25 and TF-IDF have been run against the copied source documents. LLM scoring uses the workshop's shared `OPENROUTER_API_KEY` and OpenAI-compatible chat-completions API; `LLM_BASE_URL` can point to a compatible self-hosted endpoint. Reviewed rubrics are required by default; explicitly experimental runs can use draft rubrics without marking them confirmed.

The source archive has missing and unreadable files. After restoring the collection, preparation writes an inventory report under `data/prepared/`; inspect it before running any comparison. Source-provided synthetic fit tiers are excluded from scoring and are not recruiter judgments.

## Project organization

See [implementation and verification status](docs/IMPLEMENTATION_STATUS.md) for tested features, the baseline output, and remaining configuration.

The [historical LLM experiment](docs/LIVE_LLM_RUN.md) is explicitly labeled experimental; its generated reports and CV cache remain local and are not committed.

| Stage | Folder | Purpose |
|---|---|---|
| 0 | [00-data](00-data/README.md) | Documents, extraction, confirmed requirements, and evaluation judgments |
| 1 | [01-dvc](01-dvc/README.md) | Version data and experiment artifacts |
| 2 | [02-great-expectations](02-great-expectations/README.md) | Validate inputs and outputs |
| 3 | [03-mlflow](03-mlflow/README.md) | Track and compare matching experiments |
| 4 | [04-fairlearn](04-fairlearn/README.md) | Evaluate group differences |
| 5 | [05-evidently](05-evidently/README.md) | Monitor data and ranking changes |
| 6 | [06-prefect](06-prefect/README.md) | Orchestrate the workflow |
| 7 | [07-job-matching](07-job-matching/README.md) | Run and compare the three matching methods |

The numbered stage layout adapts the MLOps workshop flow to recruitment.

## Workflow

1. Inventory and version source JDs and CVs.
2. Extract text, check readability, remove direct identity information from matching inputs where practical, and confirm each JD's job-related requirements.
3. Validate a shared candidate pool and create fixed development and held-out evaluation partitions by vacancy.
4. Run LLM, BM25, and TF-IDF independently on the same eligible documents.
5. Rank candidates within each JD and method; return five unique candidates when at least five documents can be assessed.
6. Collect independent recruiter judgments, evaluate the rankings, and inspect disagreements.
7. Record experiment artifacts, review group differences, and monitor later batches.

Prefect will own execution order. DVC will version data and artifacts rather than define a second competing orchestration pipeline.

## Shortlist contract

- Produce three separate top-five lists for every JD, one per algorithm.
- Use the same candidate pool and source text version for all methods; record method-specific preprocessing.
- Sort by descending score and break exact ties by candidate ID in ascending order. Flag ties at the cutoff.
- Never pad a list with duplicates. If fewer than five candidates are assessable, return those available and explain the shortfall.
- Distinguish top-five ranking from verified qualification. Flag unknown requirements and explicit gaps.
- Quarantine unreadable documents for review and show their exclusion in the run report.
- Preserve the full ranking, candidate pool, source references, algorithm configuration, and recruiter decisions.
- Do not compare raw score magnitudes across algorithms.

## Evaluation

Use independent, rubric-based recruiter judgments with suitable and graded-relevance labels. Keep reviewers blind to algorithm identity. Include candidates beyond the union of the three shortlists to assess missed candidates. Recall@5 requires sufficiently complete judgments; otherwise label it unavailable or explicitly limited to the judged pool.

Report Precision@5, NDCG@5, supported Recall@5, shortlist overlap, runtime, cost, and repeatability per vacancy and across job families. Compare methods on identical held-out JDs; tune only on development JDs. Synthetic or incomplete judgments do not establish real-world effectiveness.

Sensitive audit attributes must be collected appropriately, stored separately, and excluded from scoring. Do not infer them from CVs. Missing evidence is not proof of a missing skill. Recruiters retain responsibility for final decisions.

## Existing source material

The raw source folders are excluded from Git and remain in the local workspace. Restore them from a trusted USB bundle when needed:

```text
python scripts/download.py --from "D:/workshop-data"
```

Inventory these collections before combining them: their candidate identities, duplication, and vacancy associations have not yet been verified. The copied workshop repository is not part of the job-matching runtime and is not tracked here.

## Original project brief

The earlier design is preserved in [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for context. It includes supervised-model proposals; the current scope is the three-method comparison documented here.

