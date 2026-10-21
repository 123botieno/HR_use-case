# Fairness in the HR shortlist

Eight fictional vacancies and 960 fictional applications let us compare a qualification-only shortlist with a simulated historical score that penalizes gender, ethnicity, economic class, and geography. Fairlearn measures group selection rates and recall on each five-person shortlist; the exercise demonstrates a known synthetic shock, not discrimination in real hiring.

## Episodes and saved results

| Episode | Verified result from the fixed-seed run | Saved report |
|---|---|---|
| 1. A penalty hidden in a blended score | The fabricated score adds group penalties from −1 to −8 points and proxy bonuses from 0 to +5; the component columns expose each contribution. | [synthetic data](synthetic_hr_demo/synthetic_historical_hr.csv) |
| 2. The top-five cutoff changes group exposure | For gender, average selection-rate change across 8 vacancies is −1.86 percentage points for 481 women and +1.97 points for 464 men. | [gender comparison](results/precomputed/comparison_gender.json) |
| 3. Suitable candidates can be missed | Mean recall change is −6.24 points for women and +6.76 points for men. These are synthetic labels from a fixed rule, not independent recruiter judgments. | [gender comparison](results/precomputed/comparison_gender.json) |
| 4. Small groups make thin evidence | The 15 nonbinary applications average fewer than 2 people per vacancy; recall is undefined in several groups with no synthetic suitable cases. | [gender audit](results/precomputed/biased_audit_gender.json) |
| 5. One group dimension hides intersections | Audits are separate by dimension; the saved reports do not test intersections or statistical uncertainty. | [all saved comparisons](results/precomputed/) |
| 6. Complete labels do not validate decisions | All 960 suitability labels come from a fixed synthetic rule; none is a recruiter judgment. | [synthetic judgments](synthetic_hr_demo/synthetic_suitability_judgments.csv) |

All numbers above come from the committed seed-20261020 run; full per-vacancy counts and metrics are in the linked JSON reports. A change of this size is a property of the deliberately injected synthetic score recipe, not an estimate from real applicants. See [synthetic data notes](synthetic_hr_demo/README.md) and [source and license notes](data/SOURCES.md).

## Set up and run

From the repository root in PowerShell or Git Bash, with Python 3.12 and uv installed:

```text
uv venv --python 3.12 .venv
uv pip sync requirements.lock
uv run --no-sync --python 3.12 python 04-fairlearn/evaluate.py audit --run 04-fairlearn/synthetic_hr_demo/biased_historical_run.json --groups 04-fairlearn/synthetic_hr_demo/audit_groups_gender.csv --judgments 04-fairlearn/synthetic_hr_demo/synthetic_suitability_judgments.csv --output results/fairness-gender.json
```

Open [LAB_GUIDE.md](LAB_GUIDE.md) for the two-hour, CPU-only workshop sequence. The audit reads saved inputs and writes a report; no model service or external data download is needed.

## Files

- `LAB_GUIDE.md`, `FACILITATOR_NOTES.md`, `EXERCISES.md`, `INTRO_SLIDES.md`: session materials.
- `synthetic_hr.py`, `evaluate.py`: fixed-seed data generation and Fairlearn audit code.
- `synthetic_hr_demo/`: fabricated cohort, paired runs, audit labels, and judgments.
- `results/precomputed/`: committed baseline, biased, and comparison reports.
- `data/SOURCES.md`: provenance, license, and modifications.

## What Fairlearn measures

For each vacancy and model run, `MetricFrame` reports `selection_rate` for each group; when the suitability labels are complete for that vacancy, it also reports group recall. A five-person cutoff means these rates move in steps, especially for small groups. A minimum group count is a warning flag, not a confidence interval. Fairlearn calculates the chosen metrics; a human must decide which comparisons, thresholds, context, and follow-up are appropriate.

## Limits

All records, identities, group labels, scores, suitability labels, and simulated historical decisions are fabricated. Group labels are explicitly assigned in the generator and never inferred from CVs. Suitability is a transparent synthetic rule, not validated ground truth. Separate group audits do not measure intersectional effects, uncertainty, causation in real hiring, legal compliance, or whether a disparity is acceptable. Do not use this demo to make employment decisions.
