# Data sources, licenses, and synthetic assumptions

## Job descriptions

- **Source:** the repository's `Ethiopia_15_Government_JDs_750_CVs/Ethiopia_15_Public_Sector_JDs_750_CVs/` source bundle, created for the existing job-matching use case. It describes public job advertisements and records source URLs in `job_descriptions/jobs.csv`.
- **What was copied:** extracted text for the 14 available JD documents, preserving the supplied content and metadata. The upstream bundle itself describes these as source-faithful paraphrases, not verbatim advertisements. The 2nd Cook record (JD-13) had no source directory and is omitted; this gap is recorded in `job_descriptions/source_inventory_issues.csv`.
- **License:** the source bundle gives URLs but no redistribution license. The workshop includes the text already maintained in the project repository. Confirm permissions before external redistribution.

## Candidate CVs

- **Source:** the same project bundle's candidate manifest and CV files. Its README describes every CV as fictional and its fit tiers as synthetic, unvalidated screening labels.
- **What was included:** 699 readable CVs for the 14 available JDs (50 per job except JD-15, where one unreadable DOCX was omitted). Text was extracted from DOCX; generated names, application header, and direct synthetic ID were removed. Candidate IDs were generated consistently as `CV-<job number>-<candidate number>`. The unreadable CV is listed in `candidate_cvs/source_inventory_issues.csv`.
- **License:** the source bundle has no separate redistribution license. These fictional profiles contain no real applicant records or contact details, but retain source-derived text. Confirm permissions before external redistribution.

## Synthetic historical hiring file

- **Origin:** produced specifically for this workshop using `candidate_cvs/candidates.csv` as the profile inventory. Random seed: `20261022`; one row per available CV/job pair.
- **Synthetic fields:** `sex` (Woman/Man) and `geographic_location` (Addis Ababa/Outside Addis Ababa) are assigned randomly and independently of source qualification tier. They are mock audit attributes, not inferred from CVs.
- **Qualification signal:** `simulated_qualification_score` is derived from profile experience and skill-list length, plus small seeded noise. It is a fabricated teaching comparator, not validated suitability or performance ground truth. Experience, qualifications, and skill text are carried from the fictional profile index/CV.
- **Historical bias:** the simulated historical shortlist score adds a 9-point boost for Man and a 7-point boost for Addis Ababa, plus seeded noise. The score itself is not included in the participant CSV. Each job's top 10 applicants are marked historically shortlisted; the top 5 of those by simulated qualification score are marked hired. This makes the historical process intentionally group-skewed while retaining comparable qualification profiles for analysis.
- **Selective labels:** `historical_hired` is `0/1` only for shortlisted applicants and blank for those not shortlisted. `post_hire_performance` is populated only for hired applicants; `performance_observed` marks those rows. Missing values are unknown, never treated as zero or as rejection. Performance is also a synthetic teaching outcome, not measured employee performance.
- **No real data:** no real sex, location, hiring decision, or performance label was added or inferred.

## Cached LLM rankings and models

- **Origin:** `llm_precomputed_top5.csv` was derived from the existing repository run `20261015T103003Z-9124af14` and its saved `comparison_shortlists.csv`. It contains that run's top-five LLM candidate IDs and scores for 14 JDs. It is a historical cached output, not a new or live model call; only K=5 can be analyzed from it.
- **Model/source license:** refer to the existing run metadata and `07-job-matching/llm/README.md` for the project's configured provider/model. The workshop does not redistribute model weights. The live option calls the existing project `LLMScorer` through the OpenRouter-compatible endpoint and requires the workshop-provided key.
- **LLM outputs:** cached scores are method-specific and must not be compared numerically with TF-IDF or BM25. Use rank, shortlist membership, or overlap instead.

## Supporting packages

The workshop uses scikit-learn for TF-IDF, the existing project's BM25 implementation pattern, the project's LLM evidence validator/scorer for live matching, and Fairlearn for fairness metrics. Versions come from the repository's committed `requirements.lock`. The workshop source does not bundle third-party package code or model files.

## Limits

The historic score mechanism is intentionally designed to exhibit group differences. This is a controlled demonstration, not evidence of real discrimination. The group columns are marginal binary teaching categories; intersectional analysis is out of scope. Small pools and multiple differences can make estimates unstable. Source job descriptions are paraphrases and the synthetic qualification tier/score is not verified ground truth. Historical agreement cannot establish candidate quality. Post-hire performance is observed only for hired candidates, so it cannot identify how rejected/non-hired applicants would have performed.
