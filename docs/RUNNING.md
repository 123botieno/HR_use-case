# Running the job-matching comparison

Use PowerShell from the project root. Python 3.11 or newer is required.

## Environment

The implementation can use the packages already installed for the core lexical methods. For a fresh isolated setup:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

For all MLOps integrations and PDF text extraction:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-mlops.txt
```

The commands below use the virtual-environment interpreter. There is no need to activate the environment. Alternatively, after activation, use `python`. The package is runnable directly from the repository; editable installation is optional.

[requirements-tested.txt](../requirements-tested.txt) records verified direct dependency versions. Add `-c requirements-tested.txt` to installation commands to constrain those versions. This is not a full transitive lock file.

## 1. Prepare the supplied collection

```powershell
.venv/Scripts/python.exe 00-data/prepare.py --source "Ethiopia_15_Government_JDs_750_CVs/Ethiopia_15_Public_Sector_JDs_750_CVs"
.venv/Scripts/python.exe -m jobmatch validate
```

Outputs are in `data/prepared/`:

- `dataset.json`: shared matching text, paragraph references, IDs, hashes, and source associations.
- `manifest.csv`: successfully read source files.
- `inventory_issues.json`: missing, unreadable, or orphan documents.

The copied source currently yields 14 JDs and 699 CVs. JD-13 and its 50 CVs are missing; CV-15-035 is an invalid DOCX archive. Originals are unchanged. Source-provided synthetic fit tiers are neither scoring features nor evaluation judgments.

The adapter uses the supplied manifest format. The separate 250-CV collection is not automatically merged because identities and associations have not been reconciled.

## 2. Run BM25 and TF-IDF

```powershell
.venv/Scripts/python.exe 07-job-matching/run.py --methods bm25 tfidf
```

The default pool is the set of CVs associated with each JD in the source manifest. To score all 699 assessable CVs for a selected vacancy:

```powershell
.venv/Scripts/python.exe 07-job-matching/run.py --methods bm25 tfidf --pool-scope all --jd JD-01
```

Each run gets a new directory under `runs/`. The command prints that directory. Replace `RUN_ID` in later examples with its name.

## 3. Configure OpenAI and review the JD rubric

Generate draft rubric requirements from source JD sections:

```powershell
.venv/Scripts/python.exe -m jobmatch rubric-template --output data/rubric.json
```

Review and edit every requirement, split compound requirements where appropriate, set weights, and confirm the rubric by setting `confirmed` to `true` for each JD you will run. A generated draft is not a confirmed rubric.

Add your key to the project-root `.env` file as `OPENAI_API_KEY=your-key`. The command-line tool loads this file automatically; existing terminal environment variables take precedence. The file is excluded from Git. Alternatively, set your API key in the current PowerShell session:

```powershell
$secureOpenAIKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureOpenAIKey).Password
$env:OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
```

The default is the pinned model above; the environment variable can select another Responses API model with Structured Outputs support. Account availability must be checked by the account holder. The implementation uses the documented [Responses structured-output interface](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) and [model snapshot](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

Run one vacancy first:

```powershell
.venv/Scripts/python.exe 07-job-matching/run.py --rubric data/rubric.json --jd JD-01
```

Omitting `--methods` requests all three algorithms. Missing credentials, an unconfirmed rubric, API failures, unsupported models, or invalid evidence leave the run explicitly incomplete (exit code 2), while preserving successful lexical results. No lexical fallback is used for LLM failures.

LLM results are cached in `runs/llm-cache/` by input/configuration hash. Usage and cache hits are recorded. Estimated USD costs are available only if you explicitly configure current input/output rates with `OPENAI_INPUT_USD_PER_MILLION`, `OPENAI_OUTPUT_USD_PER_MILLION`, and optionally `OPENAI_CACHED_INPUT_USD_PER_MILLION`. Otherwise cost stays unavailable. API billing is not inferred from an estimate.

For an explicitly experimental run using unconfirmed draft rubrics, add `--allow-draft-rubric`. The rubrics stay unconfirmed, and the run/report records `draft_experiment`. This option does not mark them reviewed. `--llm-workers 4` enables four concurrent requests (the default is one; maximum eight).

Evidence validation may resolve a quoted passage to its unique literal source location, allowing only whitespace differences and retaining the original citation in a correction record. Unverifiable passages and invalid evidence states trigger up to two corrective OpenAI requests. Only validated evidence is scored; unresolved failures leave the affected JD/method incomplete. Repair responses and their usage are retained in the cache.

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
.venv/Scripts/python.exe 07-job-matching/comparison/evaluate.py --run runs/RUN_ID/run.json --judgments data/judgments.csv
```

Precision@5 requires every returned candidate to be judged. Recall@5 and NDCG@5 require complete pool judgments. Unavailable values stay null; no labels or performance are invented. Macro averages give each evaluated JD equal weight and report evaluated counts.

The synthetic source tiers are not independent recruiter judgments. Hold out vacancies before tuning; the current fixed baseline configurations do not fit suitability labels.

## 6. Run the MLOps stages

Great Expectations:

```powershell
.venv/Scripts/python.exe 02-great-expectations/validate.py
```

DVC requires an initialized Git/DVC repository. Initialize only in your intended repository, then version the prepared files:

```powershell
git init
.venv/Scripts/dvc.exe init
.venv/Scripts/python.exe 01-dvc/version.py --path data/prepared
```

No remote or upload is configured. DVC records local data versions; commit its pointers with your code when ready.

MLflow:

```powershell
.venv/Scripts/python.exe 03-mlflow/track.py --run runs/RUN_ID/run.json --uri sqlite:///mlflow.db
```

Fairlearn requires a separate audit CSV with `jd_id,candidate_id,group`. No sensitive groups are inferred. Add `--judgments` if appropriate labels exist:

```powershell
.venv/Scripts/python.exe 04-fairlearn/evaluate.py --run runs/RUN_ID/run.json --groups data/audit.csv --output runs/RUN_ID/audit.json
```

Evidently compares a reference and current run for the same JD/algorithm:

```powershell
.venv/Scripts/python.exe 05-evidently/monitor.py --reference runs/REFERENCE_ID/run.json --current runs/CURRENT_ID/run.json
```

Prefect coordinates validation, optional DVC, matching, evaluation, optional audits/monitoring, and MLflow tracking:

```powershell
.venv/Scripts/python.exe 06-prefect/pipeline.py --methods bm25 tfidf --gx --track-uri sqlite:///mlflow.db
```

Use `--rubric data/rubric.json` and omit `--methods` for all three methods after OpenAI setup. Optional flags: `--judgments`, `--groups`, `--reference`, and `--version-repository`. Prefect runs manually; no deployment or schedule has been created. Its temporary server may require local process/network access.

## Tests

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Unit tests use synthetic fixtures and mocked OpenAI responses. They do not incur API charges. Optional integration tests exercise installed MLOps libraries and use temporary local artifacts.

The Prefect test is opt-in because it starts a local test server:

```powershell
$env:RUN_PREFECT_TEST = "1"
.venv/Scripts/python.exe -m pytest -q -s -p no:cacheprovider
```

On this Windows environment DVC's initialization needed access to its machine cache under `C:/ProgramData/iterative`; the local DVC test passed when run with that access. No remote upload is involved.

