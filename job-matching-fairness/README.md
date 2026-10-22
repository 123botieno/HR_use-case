# Job Matching, Historical Bias, and Fairlearn Workshop

This hands-on workshop follows a fictional recruitment team as it ranks candidates for real-world-style Ethiopian public-sector vacancies. Participants compare TF-IDF, BM25, and an LLM ranking, then investigate intentionally biased synthetic hiring decisions and use Fairlearn to measure group selection differences.

The core question is: **What can we learn from ranking and fairness metrics when historical decisions may be biased and post-hire outcomes exist only for people who were hired?**

## Learning objectives

By the end, participants will be able to:

- Explain why lexical TF-IDF, BM25, and rubric-based LLM rankings differ.
- Change matching parameters and observe candidate rank and Top-K changes.
- Separate shortlisting, hiring, and post-hire performance as different events.
- Use Fairlearn `MetricFrame` to compare group selection rates, demographic parity difference, and ratio within one job's applicant pool.
- Explain why agreement with historical decisions is not evidence of correctness, and why missing performance outcomes must remain unknown.
- Make a recommendation that states both evidence and uncertainty.

## Audience and duration

For data practitioners, HR analysts, recruiters, and responsible-AI learners. Five problem-based episodes take about 2 hours. Work in pairs; no GPU is required.

## Folder structure

```text
job-matching-fairness/
├── data/
│   ├── SOURCES.md
│   ├── job_descriptions/jobs.csv
│   ├── candidate_cvs/candidates.csv
│   ├── historical_hiring_synthetic.csv
│   ├── llm_precomputed_top5.csv
│   └── generate_history.py
├── facilitator/
│   ├── FACILITATOR_NOTES.md
│   └── slides/job_matching_fairness_workshop.pptx
├── README.md
├── job_matching_helpers.py
├── requirements.lock
└── job_matching_fairness.ipynb
```

## Data

`data/job_descriptions/jobs.csv` contains the text and metadata for 14 source-faithful paraphrases of existing job descriptions. `data/candidate_cvs/candidates.csv` contains 699 fictional CV texts and profile fields for those vacancies. The 2nd Cook JD (JD-13) was unavailable in the source bundle and one JD-15 CV was unreadable. Those source gaps are recorded in `data/SOURCES.md`. The CV text has generated names, application headers, and direct synthetic IDs removed. IDs such as `JD-01` and `CV-01-001` link job text, CVs, rankings, and history. Each dataset is a single indexed CSV; there are no per-job or per-candidate subfolders.

`historical_hiring_synthetic.csv` contains one simulated applicant-job row per CV. It includes qualification/experience fields, synthetic sex and location audit fields, historical shortlist/hire decisions, post-hire performance where observed, and an explicit observation flag. It is wholly synthetic and must never be interpreted as actual recruitment data. See [data/SOURCES.md](data/SOURCES.md) for sources, assumptions, the intentional bias mechanism, and limits.

The notebook delays loading the synthetic history until Problem 3. No sex or location field is passed to a matching algorithm; those fields are only used for auditing.

## Setup

Python 3.12 and `uv` are recommended. The lock file is included in this workshop folder so this branch can be installed on its own. From the repository root:

```powershell
cd job-matching-fairness
uv venv --python 3.12 .venv
uv pip sync requirements.lock
```

Open `job_matching_fairness.ipynb` in VS Code with its Jupyter extension and select the `.venv` kernel. The notebook runs on CPU and uses the saved LLM ranking by default. To launch JupyterLab instead, install it into the same environment with `uv pip install jupyterlab`, then run `uv run jupyter lab job_matching_fairness.ipynb`.

## Run the exercises

Run notebook cells top to bottom. Each of five problems follows **Problem → Pause & Predict → Hands-on Exercise → Observe Results → Discussion → Key Takeaway**. Change one parameter at a time, keep the job and candidate pool fixed, and write down a prediction before running each comparison. The opening exercise uses `JD-01` (Senior Data Scientist); change `JOB_ID` to inspect another vacancy.

TF-IDF and BM25 return complete rankings. The packaged LLM cache contains the prior project's saved **Top 5 only** for each vacancy. Cached LLM rows are clearly marked and are not live inference; they cannot support a larger K or a parameter change. To run live LLM matching, set `OPENROUTER_API_KEY` in your shell and set `RUN_LIVE_LLM = True` in the notebook. The notebook never prints or stores the key. Live mode uses the configured model, job-related rubric, scoring instruction, temperature setting, and evidence-citation validation in the helper. LLM calls transmit CV text to the configured provider; only use the fictional workshop CVs.

If a selected model rejects a temperature parameter, leave it as `None`. In live mode, edit one rubric requirement or weight at a time. The offline cache remains unchanged when prompts or parameters change.

## Facilitation

Use [facilitator/FACILITATOR_NOTES.md](facilitator/FACILITATOR_NOTES.md) for timing, expected observations, answer guidance, and fallbacks. The slides at [facilitator/slides/job_matching_fairness_workshop.pptx](facilitator/slides/job_matching_fairness_workshop.pptx) prompt predictions and discussion; the notebook contains the detailed experiments.

## Troubleshooting

- **Import error:** confirm the selected kernel is the workshop's Python 3.12 `.venv` and sync its included `requirements.lock`.
- **CV or job not found:** keep the workshop folder intact; use IDs listed in the two `jobs.csv` and `candidates.csv` indexes.
- **TF-IDF empty vocabulary:** use the default `min_df=1`, `max_df=1.0`, then inspect whether text extraction produced content.
- **No `OPENROUTER_API_KEY`:** keep `LLM_MODE = "cached"`. The saved Top 5 results support comparison without network access.
- **Live API validation failure:** return to cached mode and discuss the saved ranking. The helper validates cited evidence and does not silently replace failed LLM output with a lexical score.
- **Fairness rates look extreme:** read the group count beside each rate, keep calculations within one job, and avoid conclusions from very small cells.
- **Missing performance values:** leave them blank/NaN. They are not zero and are not negative outcomes.

## Interpretation boundary

Fairlearn reports group differences; it does not decide whether a system is discriminatory, appropriate, or ready to use. Demographic parity is one diagnostic, not a universal hiring objective. Historical agreement measures agreement with an earlier process, not correctness. The synthetic post-hire outcomes are observed only for hired candidates, so they do not support equalized-odds evaluation for rejected or non-hired candidates. No workshop result validates a real hiring system.
