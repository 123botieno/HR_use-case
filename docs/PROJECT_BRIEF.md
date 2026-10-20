# Ethiopia Job Matching and Shortlisting

## Project objective

Create a tool that takes a job description and a batch of CVs and returns a recommended shortlist. Candidates are assessed against the same job-related criteria, with supporting evidence and missing information shown to recruiters.


## Inputs and outputs

**Inputs**

- One job description.
- A batch of candidate CVs.
- Desired shortlist size.


**Outputs**

- Candidates ranked within the vacancy.
- A recommended shortlist.
- Evidence supporting each candidate's requirement matches.
- Experience fit, skills coverage, and qualification status.
- A review queue for missing or uncertain information.
- A record of recruiter decisions and overrides.

A score represents assessed fit to the job criteria. It must not be described as a chance of job success or hiring.

## How it works

```text
Job description + CVs
          |
          v
Extract and confirm job requirements
          |
          v
LLM extracts candidate evidence
          |
          v
Create structured candidate-job features
          |
          v
Supervised model scores and ranks candidates
          |
          v
Recommended shortlist + evidence + review queue
          |
          v
Recruiter verifies and finalizes the shortlist
```

### 1. Confirm the job criteria

The LLM extracts essential skills, preferred skills, experience requirements, qualifications, certifications, tasks, and responsibility level.

Do we want a recruiter to check at this point?

### 2. Extract evidence from each CV

Assess every CV against the same confirmed requirements. Store the supporting text and its source location for each match.

Use four evidence states:

| State | Meaning |
|---|---|
| Supported | CV evidence supports the requirement |
| Explicitly not met | Available evidence establishes that the requirement is not met |
| Unknown | Evidence is missing or ambiguous |
| Not applicable | The requirement category does not apply |

Missing evidence is not proof that a candidate lacks a skill.

Use fixed extraction schemas, versioned prompts and models, and cached results. The LLM must not receive shortlist or hire outcomes during extraction. Treat CV contents as data rather than instructions.

Check document extraction, OCR, dates, and language coverage. Unreadable documents require review rather than an automatic low score.

### 3. Construct the feature dataset

Each row represents one candidate applying for one job.

| Feature | Description |
|---|---|
| Essential skills coverage | Fraction of essential skills supported by evidence |
| Preferred skills coverage | Fraction of preferred skills supported by evidence |
| Missing essential evidence | Count of essential requirements with unknown status |
| Essential requirements not met | Count of essential requirements explicitly not met |
| Relevant experience years | Experience relevant to the vacancy, without double-counting overlapping roles |
| Skill-specific experience | Experience using individual required skills |
| Experience fit percentage | Difference from the stated experience requirement |
| Experience fit status | Below minimum, meets minimum, within range, above range, or unknown |
| Task experience coverage | Evidence of performing the job's tasks |
| Responsibility level match | Alignment of candidate responsibilities with the role |
| Tools and methods coverage | Evidence of required tools, equipment, or methods |
| Education status | Requirement or approved alternative supported |
| Certification status | Required certification supported |
| Required language status | Evidence of a confirmed job-related language requirement |
| Semantic similarity | Optional embedding similarity between job-related CV and vacancy text |

Retain raw values, requirement definitions, coverage denominators, and evidence alongside aggregate features. An absent requirement category is not applicable, not zero coverage.

Semantic similarity captures related terminology but does not establish qualification. Evaluate models with and without it.

### Experience fit

For a positive minimum experience requirement:

```text
experience_gap_pct =
    ((relevant_years - required_min_years) / required_min_years) * 100
```

For a job requiring at least five years:

| Relevant experience | Percentage gap | Interpretation |
|---|---:|---|
| 3 years | -40% | Below minimum |
| 5 years | 0% | Meets minimum |
| 7 years | +40% | Meets minimum; exceeds it by 40% |

Exceeding a minimum does not mean a candidate is overqualified. Do not automatically penalize additional experience.

For a stated three-to-five-year range:

| Relevant experience | Range deviation | Status |
|---|---:|---|
| 2 years | -33.3% relative to the lower bound | Below range |
| 4 years | 0% | Within range |
| 6 years | +20% relative to the upper bound | Above range |

Store range deviation separately from minimum-gap percentage. Above-range experience does not automatically imply unsuitability.

If no positive requirement is stated, the percentage is undefined. If dates or relevance are unclear, use unknown and request verification. Being below a requirement should trigger automatic exclusion only when the criterion is confirmed mandatory and the evidence is reliable.

## Supervised training approach

### Available historical dataset

Assume we have CVs, linked job descriptions, shortlist outcomes, and hire outcomes.

| Field | Purpose |
|---|---|
| application_id | Unique application |
| candidate_id | Pseudonymous identifier for repeat applicants |
| job_id | Vacancy identifier |
| recruitment_round_id | Recruitment campaign or round |
| application_date | Time-based evaluation |
| cv_text | CV as submitted |
| job_description_text | Job description available at application time |
| shortlisted | Historical shortlist label |
| hired | Historical hire label |
| process_status | Completed, pending, withdrawn, or unclear |

Include unsuccessful applications. Do not automatically label pending cases or withdrawals before assessment as unsuitable.

### Initial historical models

Use the extracted features to train separate models for:

- Historical shortlisting: `P(shortlisted | CV, job description)`.
- Historical hiring: `P(hired | CV, job description)`, as a later experiment.

These models are useful for evaluating whether the features predict recorded outcomes and understanding existing recruitment patterns. They can also reproduce biases in past decisions.



### ModelLING


## Shortlist decision rules

Rank candidates within each vacancy using the suitability score and the confirmed requirement rules.

- Return up to the requested shortlist size among candidates meeting the agreed threshold.
- Return fewer candidates if too few meet that threshold.
- Route ambiguous evidence and ties at the cutoff for recruiter review.
- Keep candidates outside the recommended shortlist available for inspection.
- Record the final shortlist and reasons for overrides.

A missing certification statement, for example, should prompt verification rather than being treated as a confirmed absence.

## Evaluation

Test on unseen vacancies and report results by job family as well as overall.

| Measure | What it evaluates |


For historical models, calculate prediction metrics against their historical labels and label those results clearly. Historical agreement is not proof of suitability or fairness.

Compare against the requirement baseline and semantic similarity alone. Define shortlist size and thresholds before final testing. Report sample counts and uncertainty.

## Bias prevention and audit

The objective is to reduce and detect bias, not claim that the tool is inherently bias-free.

### Scoring inputs

Remove names, photographs, gender, community identity, and direct identifiers before extraction where practical. Do not use sensitive attributes as scoring features.

Exclude school prestige, career gaps, employment status, CV writing style, salary history, and job-change counts from the first model. Review potential proxies such as institution names, geography, and language. Location and language criteria require a documented job-related purpose.

### Audit data

Store appropriately collected gender and community categories separately from scoring data, with restricted access. Define what community means for this project. Do not infer these attributes from CVs.

### Audit measures

Assess within comparable vacancies:

- Recommendation rates and top-K exposure by group.
- Recall and false-negative rates among independently assessed suitable candidates.
- Extraction errors, missing evidence, and review routing by group and CV language.
- Intersecting groups where samples support reliable analysis.
- Changes in scores or rankings when irrelevant identity cues change while qualifications remain fixed.
- Recruiter overrides and final selection outcomes.

Removing sensitive fields alone does not eliminate bias. Equal recommendation rates alone do not prove fairness. Report group counts and uncertainty; small or missing samples mean evidence is insufficient.

Agree on fairness measures, acceptable disparities, and remediation rules before final testing. Investigate requirements, labels, extraction, features, and thresholds when disparities appear, then revise and re-evaluate.

## Example recruiter output

| Candidate | Experience fit | Requirement evidence | Recommendation |
|---|---|---|---|
| A | Meets five-year minimum | Essential requirements supported | Shortlist if above threshold |
| B | 40% above minimum | Essential requirements supported | Shortlist if above threshold |
| C | 20% below minimum | Strong skill evidence; experience criterion needs review | Review |

These examples illustrate evidence handling, not a fixed model decision. Final recommendations depend on the full rubric, validated score, and shortlist capacity.

Each recommendation includes source passages and distinguishes explicit gaps from missing information. Evidence summaries explain requirement matching; they must not imply they explain every model contribution unless that relationship has been verified.

## First-outcome deliverables

1. Audited historical dataset and documented outcome definitions.
2. Confirmed qualification rubric and independently reviewed sample.
3. Versioned feature dictionary, extraction schema, prompts, and evidence records.
4. Requirement baseline, historical prediction experiment, and suitability model.
5. Held-out performance, extraction-quality, and bias evaluation report.
6. Shadow-mode shortlist workflow with recruiter feedback.
7. A documented decision to proceed, revise, or stop.

Agree on minimum useful performance, acceptable disparities, extraction quality, review capacity, and pause criteria before training. Operational use follows evaluation and a reviewed deployment decision.

## Later work

Extend the pilot to additional job families after validation. Investigate historical hiring outcomes separately, distinguishing offers, acceptance, and starts where available.

Hiring reflects interviews, competition, candidate choices, and employer decisions. Predicting actual job performance would require separate, reliable performance data and its own validation.
