# HR shortlisting fairness

This use case asks how historical hiring decisions can teach a shortlist model to repeat past bias. It also shows why outcomes recorded only for shortlisted candidates leave the rest of the applicant pool unevaluated.

## Walkthrough episodes

| Episode | What the run shows | Saved output |
|---|---|---|
| 1. Historical decisions carry a score penalty | The simulated score adds explicit gender, ethnicity, class, and geography penalties plus access-proxy bonuses. | [`synthetic_historical_hr.csv`](04-fairlearn/synthetic_hr_demo/synthetic_historical_hr.csv) |
| 2. Unseen outcomes are not rejections | In the fixed-seed cohort, 40 of 960 applications have an observed historical hiring outcome; 920 are blank because they were not shortlisted. | [`metadata.json`](04-fairlearn/synthetic_hr_demo/metadata.json) |
| 3. A top-five cutoff changes group access | The gender selection-rate shift is summarized across 8 fictional vacancies, with counts beside each group rate. | [saved gender comparison](04-fairlearn/results/precomputed/comparison_gender.json) |
| 4. A disparity is a prompt to investigate | The comparison also shows synthetic suitability recall, small-group counts, and the limits of marginal audits. | [saved audit reports](04-fairlearn/results/precomputed/) |

All numbers are from the fixed-seed synthetic run and are described with their denominator in the saved outputs. The outcomes and group labels are simulated. `historical_hired` is blank when it was not observed; it is never converted to a negative label for non-shortlisted applicants. The separate `suitable` field is a fully synthetic teaching label, not a historical hiring outcome or recruiter judgment.

## Set up and run

Use Python 3.12 and the shared hub lock file. From the repository root:

```text
uv venv --python 3.12 .venv
uv pip sync requirements.lock
code 04-fairlearn/HR_Fairness_Learning_Session.ipynb
```

The third command opens the 2-hour, CPU-only learning session in VS Code. Select the repository's Python 3.12 environment as the notebook kernel. No API key or network access is needed for this fairness walkthrough. The separate matching demonstration uses the shared `OPENROUTER_API_KEY` through OpenRouter; see [`.env.example`](.env.example).

## Files

- [Fairness learning notebook](04-fairlearn/HR_Fairness_Learning_Session.ipynb): four episodes with PAUSE prompts, Fairlearn code, fixes, and checks.
- [Facilitator notes](04-fairlearn/FACILITATOR_NOTES.md), [exercises](04-fairlearn/EXERCISES.md), and [intro slides](04-fairlearn/INTRO_SLIDES.md).
- [`04-fairlearn/synthetic_hr.py`](04-fairlearn/synthetic_hr.py) and [`evaluate.py`](04-fairlearn/evaluate.py): generated cohort and Fairlearn metrics.
- [`synthetic_hr_demo/`](04-fairlearn/synthetic_hr_demo/): fictional data, rankings, group labels, and outcome-observation metadata.
- [`results/precomputed/`](04-fairlearn/results/precomputed/): saved baseline, biased, and comparison reports.
- [`data/SOURCES.md`](data/SOURCES.md): data provenance, license, and modifications.

## MLOps workshop

This repo keeps the HR-specific fairness and shortlisting story. For shared lessons on DVC, Great Expectations, MLflow, Prefect, and other MLOps tools, use the workshop hub and its setup guide. The hub link and shared slide template were not present in this checkout; add the canonical links when available.

## Interpretation

Fairlearn's `MetricFrame` computes group selection rates and, when the independent synthetic suitability labels are complete, recall. A person must choose which fairness question and follow-up matter for the hiring context. Small cells, incomplete real outcomes, unvalidated labels, and separate marginal audits limit conclusions; passing these synthetic checks is not evidence that real hiring is fair.
