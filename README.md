# Ethiopia Job Matching and Shortlisting

Compare LLM, BM25, and TF-IDF on the same candidate pool for each job description (JD). Each method returns its own ranked shortlist of five candidates. Recruiters review suitability and evidence; a ranking score is not a probability of hiring or job success.

## Project status

Python implementations now cover document preparation, BM25, TF-IDF, OpenAI LLM evidence scoring, top-five selection, judgment-based evaluation, and optional DVC, Great Expectations, MLflow, Fairlearn, Evidently, and Prefect integrations. Each stage folder contains its implementation and runnable command. Only file I/O, tokenization, and numbered-folder loading live in `common/`; `jobmatch/` contains the shared CLI dispatcher.

See [the running guide](docs/RUNNING.md) for setup and commands. BM25 and TF-IDF have been run against the copied source documents. OpenAI scoring reads `OPENAI_API_KEY` from the environment or the project-root `.env`. Reviewed rubrics are required by default; explicitly experimental runs can use draft rubrics without marking them confirmed.

The copied source is incomplete: JD-13 and its 50 CVs are missing, and CV-15-035 is not a valid DOCX archive. Preparation records 52 issues and produces 14 JDs and 699 assessable CVs. Synthetic fit tiers are excluded from scoring and are not used as recruiter judgments.

## Project organization

See [implementation and verification status](docs/IMPLEMENTATION_STATUS.md) for tested features, the baseline output, and remaining configuration.

The [live OpenAI experiment](docs/LIVE_LLM_RUN.md) has completed for all 14 available JDs and 699 CVs, with five-candidate shortlists from all three methods. It uses unconfirmed draft rubrics and is explicitly labeled experimental.

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

The organization follows the locally copied [MLOps Workshop](MLOps-Workshop-main/MLOps-Workshop-main/README.md), adapted to recruitment.

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

The existing source folders remain in place:

- `Ethiopia_15_Government_JDs_750_CVs/`
- `Ethiopia_250_Detailed_WORD_CVs/`

Inventory these collections before combining them: their candidate identities, duplication, and vacancy associations have not yet been verified. The copied workshop remains a reference, not part of the job-matching runtime.

## Original project brief

The earlier design is preserved in [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) for context. It includes supervised-model proposals; the current scope is the three-method comparison documented here.

