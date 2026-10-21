# Running the job-matching comparison

Use PowerShell or Git Bash from the project root. Python 3.12 and uv are required.

## Environment

Create a fresh isolated environment and install the complete, transitive lock:

```powershell
uv venv --python 3.12 .venv
uv pip sync requirements.lock
```

Activate the environment once: in PowerShell run `.\.venv\Scripts\Activate.ps1`; in Git Bash run `source .venv/Scripts/activate`. After that, the commands below use `python` in either shell. For the lexical demo, no LLM credentials are needed. The local raw collections are not stored in Git; restore them from a trusted USB bundle when needed:

```powershell
python scripts/download.py --from "D:/workshop-data"
```

The manifest verifies all restored files by SHA-256. See [data source and license notes](../data/SOURCES.md) before using the supplied CV collection. The package is runnable directly from the repository; editable installation is optional.

## 1. Restore and prepare the supplied collection

After restoring the source files with `scripts/download.py` as above:

```powershell
python 00-data/prepare.py --source "Ethiopia_15_Government_JDs_750_CVs/Ethiopia_15_Public_Sector_JDs_750_CVs"
python -m jobmatch validate
```

Outputs are in `data/prepared/`:

- `dataset.json`: shared matching text, paragraph references, IDs, hashes, and source associations.
- `manifest.csv`: successfully read source files.
- `inventory_issues.json`: missing, unreadable, or orphan documents.

The copied source currently yields 14 JDs and 699 CVs. JD-13 and its 50 CVs are missing; CV-15-035 is an invalid DOCX archive. Originals are unchanged. Source-provided synthetic fit tiers are neither scoring features nor evaluation judgments.

The adapter uses the supplied manifest format. The separate 250-CV collection is not automatically merged because identities and associations have not been reconciled.

## 2. Run BM25 and TF-IDF

```powershell
python 07-job-matching/run.py --methods bm25 tfidf
```

The default pool is the set of CVs associated with each JD in the source manifest. To score all 699 assessable CVs for a selected vacancy:

```powershell
python 07-job-matching/run.py --methods bm25 tfidf --pool-scope all --jd JD-01
```

Each run gets a new directory under `runs/`. The command prints that directory. Replace `RUN_ID` in later examples with its name.

## 3. Configure OpenRouter and review the JD rubric

Generate draft rubric requirements from source JD sections:

```powershell
python -m jobmatch rubric-template --output data/rubric.json
```

Review and edit every requirement, split compound requirements where appropriate, set weights, and confirm the rubric by setting `confirmed` to `true` for each JD you will run. A generated draft is not a confirmed rubric.

Copy `.env.example` to `.env` and add the workshop's shared key as `OPENROUTER_API_KEY=...`. The command-line tool loads this file automatically; existing terminal environment variables take precedence. The file is excluded from Git. Alternatively, set the key in the current PowerShell session:

```powershell
$secureRouterKey = Read-Host "Workshop OpenRouter key" -AsSecureString
$env:OPENROUTER_API_KEY = [System.Net.NetworkCredential]::new("", $secureRouterKey).Password
$env:OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"
```

The default is the configured open-weight model above. `OPENROUTER_MODEL` selects another model available to the workshop key. The client uses OpenRouter's OpenAI-compatible chat-completions API and JSON-schema response format. Set `LLM_BASE_URL` to a compatible self-hosted chat-completions endpoint when needed. Model availability and structured-output support depend on the selected provider and model.

Run one vacancy first:

```powershell
python 07-job-matching/run.py --rubric data/rubric.json --jd JD-01
```

Omitting `--methods` requests all three algorithms. Missing credentials, an unconfirmed rubric, API failures, unsupported models, or invalid evidence leave the run explicitly incomplete (exit code 2), while preserving successful lexical results. No lexical fallback is used for LLM failures.

LLM results are cached in `runs/llm-cache/` by input/configuration hash. Usage and cache hits are recorded. Estimated USD costs are available only if you explicitly configure current input/output rates with `OPENROUTER_INPUT_USD_PER_MILLION`, `OPENROUTER_OUTPUT_USD_PER_MILLION`, and optionally `OPENROUTER_CACHED_INPUT_USD_PER_MILLION`. Otherwise cost stays unavailable. API billing is not inferred from an estimate.

For an explicitly experimental run using unconfirmed draft rubrics, add `--allow-draft-rubric`. The rubrics stay unconfirmed, and the run/report records `draft_experiment`. This option does not mark them reviewed. `--llm-workers 4` enables four concurrent requests (the default is one; maximum eight).

Evidence validation may resolve a quoted passage to its unique literal source location, allowing only whitespace differences and retaining the original citation in a correction record. Unverifiable passages and invalid evidence states trigger up to two corrective chat-completions requests. Only validated evidence is scored; unresolved failures leave the affected JD/method incomplete. Repair responses and their usage are retained in the cache.

Automatic document chunking and OCR are not implemented; oversized or unreadable inputs are explicitly rejected.

## 4. Inspect outputs

- `run.json`: configurations, pool hashes, full rankings, per-method status, evidence, and runtime.
- `rankings.csv`: complete rankings.
- `shortlists.csv`: five candidates per JD and successful algorithm.
- `comparison_shortlists.csv`: the methods' candidates and scores in adjacent columns.
- `report.md`: human-readable top-five report and failure reasons.
- `comparison.json`: overlap, timing, and available judgment-based metrics.
- `judgments_template.csv`: full-pool blind-review IDs with blank labels.

Ranking ties break by ascending candidate ID and cutoff ties are flagged. A top-five list is a relevance ranking, not verified eligibility. Fewer than five assessable candidates produce a shortfall.

## 5. Evaluate with independent judgments

Copy `judgments_template.csv` to `data/judgments.csv` and fill independent recruiter assessments. The rubric uses suitable=0/1 and relevance=0..3; zero means unsuitable, and 1..3 represent increasing suitability. Partially completed rows with missing labels are invalid; entirely blank rows remain unjudged.

```powershell
python 07-job-matching/comparison/evaluate.py --run runs/RUN_ID/run.json --judgments data/judgments.csv
```

Precision@5 requires every returned candidate to be judged. Recall@5 and NDCG@5 require complete pool judgments. Unavailable values stay null; no labels or performance are invented. Macro averages give each evaluated JD equal weight and report evaluated counts.

The synthetic source tiers are not independent recruiter judgments. Hold out vacancies before tuning; the current fixed baseline configurations do not fit suitability labels.

## 6. Run the MLOps stages

Great Expectations:

```powershell
python 02-great-expectations/validate.py
```

DVC requires an initialized Git/DVC repository. Initialize only in your intended repository, then version the prepared files:

```powershell
git init
.venv/Scripts/dvc.exe init
python 01-dvc/version.py --path data/prepared
```

No remote or upload is configured. DVC records local data versions; commit its pointers with your code when ready.

MLflow:

```powershell
python 03-mlflow/track.py --run runs/RUN_ID/run.json --uri sqlite:///mlflow.db
```

Fairlearn requires a separate audit CSV with `jd_id,candidate_id,group`. No sensitive groups are inferred. Add `--judgments` if appropriate labels exist:

```powershell
python 04-fairlearn/evaluate.py --run runs/RUN_ID/run.json --groups data/audit.csv --output runs/RUN_ID/audit.json
```

Evidently compares a reference and current run for the same JD/algorithm:

```powershell
python 05-evidently/monitor.py --reference runs/REFERENCE_ID/run.json --current runs/CURRENT_ID/run.json
```

Prefect coordinates validation, optional DVC, matching, evaluation, optional audits/monitoring, and MLflow tracking:

```powershell
python 06-prefect/pipeline.py --methods bm25 tfidf --gx --track-uri sqlite:///mlflow.db
```

Use `--rubric data/rubric.json` and omit `--methods` for all three methods after OpenRouter setup. Optional flags: `--judgments`, `--groups`, `--reference`, and `--version-repository`. Prefect runs manually; no deployment or schedule has been created. Its temporary server may require local process/network access.

## Tests

```powershell
python -m pytest -q -p no:cacheprovider
```

Unit tests use synthetic fixtures and mocked chat-completions responses. They do not incur API charges. Optional integration tests exercise installed MLOps libraries and use temporary local artifacts.

The Prefect test is opt-in because it starts a local test server:

```powershell
$env:RUN_PREFECT_TEST = "1"
python -m pytest -q -s -p no:cacheprovider
```

On this Windows environment DVC's initialization needed access to its machine cache under `C:/ProgramData/iterative`; the local DVC test passed when run with that access. No remote upload is involved.

