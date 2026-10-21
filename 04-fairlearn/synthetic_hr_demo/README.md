# Synthetic historical HR fairness demonstration

> **Entirely fictional teaching data.** No records in this folder describe real applicants, employees, protected groups, hiring decisions, or measured discrimination. Do not use it for employment decisions or as evidence about fairness in Ethiopia.

## What it contains

The fixed-seed generator creates 960 synthetic applications: 8 fictional vacancies with 120 applicants each. Qualification features are generated independently of group membership. A transparent rule creates synthetic suitability labels so that fairness metrics can be exercised without recruiter data.

It creates two rankings over the same applications:

- `qualification_baseline_run.json`: ranks using a synthetic job-related qualification score.
- `biased_historical_run.json`: ranks using that score plus explicit group penalties and access-proxy bonuses, representing a deliberately biased historical process.

The historical score recipe is visible in `synthetic_historical_hr.csv` as separate score-effect columns. It applies penalties by gender, ethnicity, economic class, and geography. It also gives bonuses for elite-access and advanced-English proxies; their generated prevalence differs across class and geography groups. The top five by each score become the shortlist. A random 35% of those shortlisted by the biased historical score are marked as hired. `historical_hired` is blank for the other 920 applicants: their hiring outcome was not observed, so they are not labeled as rejected.

The suitability rule is separate from those historical decisions: skill match at least 62, at least three relevant years, and required certificate present. It does not use group values. These labels are still synthetic and are not independently verified ground truth.

## Files

| File | Purpose |
|---|---|
| `synthetic_historical_hr.csv` | Application features, four group dimensions, objective qualification score, deliberately biased historical score, explicit bias components, synthetic suitability, and shortlist/hire outcomes with unobserved hires left blank. |
| `qualification_baseline_run.json` | Fairness audit input for the qualification baseline ranking. |
| `biased_historical_run.json` | Fairness audit input for the simulated biased historical ranking. |
| `synthetic_suitability_judgments.csv` | Complete synthetic suitable/relevance labels used only to demonstrate group recall. |
| `audit_groups_gender.csv` | Gender audit labels keyed by vacancy and synthetic candidate ID. |
| `audit_groups_ethnicity.csv` | Synthetic ethnicity category audit labels. Categories are placeholders, not real ethnic identities. |
| `audit_groups_economic_class.csv` | Synthetic economic-class audit labels. |
| `audit_groups_geography.csv` | Synthetic geography audit labels. |
| `audit_<dimension>/` | Fairlearn baseline audit, historical audit, and paired comparison for each dimension. |
| `metadata.json` | Seed, cohort sizes, bias recipe, synthetic suitability definition, and interpretation limits. |

## Reproduce

From the project root, regenerate the same cohort:

```powershell
uv run --no-sync --python 3.12 python 04-fairlearn/synthetic_hr.py --output 04-fairlearn/synthetic_hr_demo --seed 20261020 --vacancies 8 --applicants-per-vacancy 120
```

To run or refresh one dimension's Fairlearn comparison (repeat with `ethnicity`, `economic_class`, and `geography` to rebuild the other reports):

```text
uv run --no-sync --python 3.12 python 04-fairlearn/evaluate.py compare-synthetic --baseline 04-fairlearn/synthetic_hr_demo/qualification_baseline_run.json --biased 04-fairlearn/synthetic_hr_demo/biased_historical_run.json --groups 04-fairlearn/synthetic_hr_demo/audit_groups_gender.csv --judgments 04-fairlearn/synthetic_hr_demo/synthetic_suitability_judgments.csv --output 04-fairlearn/synthetic_hr_demo/audit_gender/comparison.json
```

The comparison writes `baseline_audit.json`, `biased_audit.json`, and `comparison.json` under each dimension's output folder. Fairlearn reports selection rate and recall per vacancy and group. Check counts and `sufficient_sample`; the rare synthetic Nonbinary category is intentionally too small for strong conclusions in many vacancies.

## Interpretation

The paired comparison holds vacancy, candidate IDs, group labels, and synthetic suitability labels fixed. Only the score source changes. Differences in shortlist rate or recall therefore show that the injected historical scoring recipe can change measured outcomes in this constructed cohort. Since the recipe directly includes group penalties and proxies, this is a software demonstration of detection, not a discovery about real hiring.

The four dimensions are audited separately. This demo does not estimate uncertainty, run significance tests, examine intersections between all four dimensions, infer causality from real data, or determine whether a disparity is acceptable. Replace mock groups and labels with appropriately collected restricted audit data and independent recruiter judgments before drawing real-world conclusions.
