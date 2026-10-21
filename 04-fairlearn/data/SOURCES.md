# Data and model sources

## Synthetic fairness cohort

- **Origin:** generated locally by [`synthetic_hr.py`](../synthetic_hr.py); no external dataset or model is used to create the cohort or score candidates.
- **License:** generated in this repository; no third-party dataset license applies. The repository has no top-level license file, so reuse terms for the generator and its outputs have not been formally granted.
- **Fixed seed:** `20261020`; default size is 8 fictional vacancies × 120 applications = 960.
- **Changes:** all IDs, groups, qualification fields, group penalties, proxy values, suitability labels, rankings, and observed hire outcomes are generated. Group categories are fictional placeholders. The suitability rule is `skill_match >= 62`, `relevant_years >= 3`, and certificate present. The historical score injects group penalties and proxy bonuses deliberately. Hire outcomes are generated only for the 40 shortlisted applicants; the other 920 values are missing, not negative labels.
- **Model:** none. The output is a deterministic rule-based teaching scenario, not a trained or deployed hiring model.
- **Downloads:** none; no raw applicant records are required. `downloads.json` is empty by design.

## Fairlearn and supporting packages

Fairlearn, pandas, and scikit-learn are third-party open-source dependencies installed from the Python package index at versions pinned in the repository lock. Consult each package's upstream license and the selected version's package metadata for redistribution or legal use; this teaching repo does not bundle their code.

## Use restrictions and limits

These records do not describe real applicants, employees, protected groups, or decisions. They cannot substantiate a claim about discrimination, validate a real hiring process, or support an employment decision. No CV text, commercial LLM, or external model contributed to this dataset.
