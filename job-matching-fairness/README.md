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
│   ├── job_descriptions/
│   ├── candidate_cvs/
│   ├── historical_hiring_synthetic.csv
│   └── llm_precomputed_top5.csv
├── facilitator/
│   ├── FACILITATOR_NOTES.md
│   └── slides/job_matching_fairness_workshop.pptx
├── README.md
├── job_matching_helpers.py
└── job_matching_fairness.ipynb
```

## Data

`data/job_descriptions/jobs.csv` indexes 14 source-faithful paraphrases of existing job descriptions, with job ID, title, employer, sector, level, and source URL. `data/candidate_cvs/candidates.csv` indexes 699 fictional CVs across the same 14 jobs. JD-13 has no source folder, and one CV in JD-15 was unreadable; both gaps are documented in inventory files. Each CV is stored as plain text with the generated name, application header, and direct synthetic ID removed. IDs such as `JD-01` and `CV-01-001` link job text, CVs, rankings, and history.

`historical_hiring_synthetic.csv` contains one simulated applicant-job row per CV. It includes qualification/experience fields, synthetic sex and location audit fields, historical shortlist/hire decisions, post-hire performance where observed, and an explicit observation flag. It is wholly synthetic and must never be interpreted as actual recruitment data. See [data/SOURCES.md](data/SOURCES.md) for sources, assumptions, the intentional bias mechanism, and limits.

The notebook delays loading the synthetic history until Problem 3. No sex or location field is passed to a matching algorithm; those fields are only used for auditing.

## Setup

Python 3.12 and `uv` are recommended. Run from the repository root so the workshop can use the shared project lock file:

```powershell
uv venv --python 3.12 .venv
uv pip sync requirements.lock
```

Then open `job-matching-fairness/job_matching_fairness.ipynb` in Jupyter or VS Code and select the repository `.venv` kernel. Alternatively, from this folder install the same locked Fairlearn, pandas, scikit-learn, and matplotlib versions via `uv pip install -r ../requirements.lock`.

## Run the exercises

Run notebook cells top to bottom. Each of five problems follows **Problem → Pause & Predict → Hands-on Exercise → Observe Results → Discussion → Key Takeaway**. Change one parameter at a time, keep the job and candidate pool fixed, and write down a prediction before running each comparison. The opening exercise uses `JD-01` (Senior Data Scientist); change `JOB_ID` to inspect another vacancy.

TF-IDF and BM25 return complete rankings. The packaged LLM cache contains the prior project's saved **Top 5 only** for each vacancy. Cached LLM rows are clearly marked and are not live inference; they cannot support a larger K or a parameter change. To run live LLM matching, use the shared OpenRouter key as `OPENROUTER_API_KEY` in the environment and set `LLM_MODE = "live"` in the notebook. The notebook never prints or stores the key. Live mode uses the project's existing evidence-validation scorer. Its model, rubric weights, scoring instruction, and supported temperature are visible in the helper call. LLM calls transmit CV text to the configured provider; only use the fictional workshop CVs.

The existing project scorer supports temperature only in the workshop wrapper's custom-prompt path. If a selected model rejects a temperature parameter, leave it as `None`. In live mode, edit one rubric requirement or weight at a time. The offline cache remains unchanged when prompts or parameters change.

## Facilitation

Use [facilitator/FACILITATOR_NOTES.md](facilitator/FACILITATOR_NOTES.md) for timing, expected observations, answer guidance, and fallbacks. The slides at [facilitator/slides/job_matching_fairness_workshop.pptx](facilitator/slides/job_matching_fairness_workshop.pptx) prompt predictions and discussion; the notebook contains the detailed experiments.

## Troubleshooting

- **Import error:** confirm the selected kernel is the repository Python 3.12 environment and install from the shared lock file.
- **CV or job not found:** keep the workshop folder intact; use IDs listed in the two `jobs.csv` and `candidates.csv` indexes.
- **TF-IDF empty vocabulary:** use the default `min_df=1`, `max_df=1.0`, then inspect whether text extraction produced content.
- **No `OPENROUTER_API_KEY`:** keep `LLM_MODE = "cached"`. The saved Top 5 results support comparison without network access.
- **Live API validation failure:** return to cached mode and discuss the saved ranking. The project scorer validates cited evidence and does not silently replace failed LLM output with a lexical score.
- **Fairness rates look extreme:** read the group count beside each rate, keep calculations within one job, and avoid conclusions from very small cells.
- **Missing performance values:** leave them blank/NaN. They are not zero and are not negative outcomes.

## Interpretation boundary

Fairlearn reports group differences; it does not decide whether a system is discriminatory, appropriate, or ready to use. Demographic parity is one diagnostic, not a universal hiring objective. Historical agreement measures agreement with an earlier process, not correctness. The synthetic post-hire outcomes are observed only for hired candidates, so they do not support equalized-odds evaluation for rejected or non-hired candidates. No workshop result validates a real hiring system.
