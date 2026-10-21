# Fairness in the HR shortlist

This session shows how a model trained on historical hiring decisions can carry their bias forward. It also shows that hire outcomes observed only for shortlisted people cannot tell us which excluded applicants would have succeeded.

## Episodes and verified outputs

| Episode | Run evidence | Saved output |
|---|---|---|
| 1. Historical decisions carry a score penalty | Group penalties and access-proxy bonuses are explicit columns in the fixed-seed cohort. | [`synthetic_historical_hr.csv`](synthetic_hr_demo/synthetic_historical_hr.csv) |
| 2. Missing outcomes are not negative labels | 40 of 960 applications have observed hire outcomes; 920 are blank because they were not shortlisted. | [`metadata.json`](synthetic_hr_demo/metadata.json) |
| 3. The cutoff changes group access | Gender selection rates are compared across 8 synthetic vacancies, with application counts shown. | [`comparison_gender.json`](results/precomputed/comparison_gender.json) |
| 4. Recall needs independent outcome evidence | Saved recall uses complete fabricated suitability labels; real hire outcomes are missing for non-shortlisted people. | [saved comparisons](results/precomputed/) |

Figures come from seed `20261020`; the saved outputs preserve per-vacancy values. Every row and label is synthetic. The `historical_hired` field is empty when the hiring outcome was not observed. The separate `suitable` label is generated for this exercise and is not hiring history or validated ground truth.

## Setup and run

Use Python 3.12 and the shared hub `requirements.lock` from the repository root:

```text
uv venv --python 3.12 .venv
uv pip sync requirements.lock
uv run --no-sync --python 3.12 python 04-fairlearn/evaluate.py audit --run 04-fairlearn/synthetic_hr_demo/biased_historical_run.json --groups 04-fairlearn/synthetic_hr_demo/audit_groups_gender.csv --judgments 04-fairlearn/synthetic_hr_demo/synthetic_suitability_judgments.csv --output 04-fairlearn/results/fairness-gender.json
```

Open the [four-episode learning notebook](HR_Fairness_Learning_Session.ipynb) in VS Code and select the repository's Python 3.12 environment as its kernel. It runs on a CPU laptop and links to saved results for discussion without rerunning calculations.

## Contents and limits

- [`synthetic_hr.py`](synthetic_hr.py) generates the cohort; [`evaluate.py`](evaluate.py) uses Fairlearn `MetricFrame` for group selection rate and, where labels are complete, recall.
- [`synthetic_hr_demo/`](synthetic_hr_demo/) contains the generated data, group tables, ranking runs, and metadata.
- [`results/precomputed/`](results/precomputed/) contains saved baseline, simulated historical, and comparison audits.
- [Facilitator notes](FACILITATOR_NOTES.md), [exercises](EXERCISES.md), and [intro slides](INTRO_SLIDES.md) support the notebook session.
- [`data/SOURCES.md`](data/SOURCES.md) records provenance and changes.

The labels, identities, score shock, and decisions are fictional. Small groups make rates unstable; the saved exercise has no uncertainty estimates, real recruiter labels, or intersectional audit. Fairlearn computes selected metrics; people must decide the relevant measure, acceptable evidence, and response.
