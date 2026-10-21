# Fairness in the HR shortlist: lab guide

**Time:** 2 hours. **Runs on:** CPU laptop, Python 3.12. **Data:** fictional and generated with a fixed seed. **Tools:** pandas, scikit-learn, Fairlearn `MetricFrame`; no LLM request.

Start at the repository root. Use the three setup commands in [README.md](README.md). The generated cohort and saved reports are in `04-fairlearn/synthetic_hr_demo/` and `04-fairlearn/results/precomputed/`. The commands use `uv run` and work in PowerShell and Git Bash.

## 1. A qualification baseline has no group term (15 min)

**Do the obvious thing.** Rank by the fabricated job-related qualification score. Inspect the baseline report and the score columns in `synthetic_historical_hr.csv`.

**See the problem.** The top five are only five places per vacancy; a single rank change can move the group rate by several percentage points. The baseline gender audit has 8 vacancy-level comparisons and reports the selection rate against each group's application count.

**PAUSE — 3 min:** What denominator would you use to compare shortlist access: all applications, only qualified applications, or another set? Write down why before reading on.

**The fix and the human decision.** Keep the denominator tied to the question: selection rate uses all audited applications; recall uses all synthetically suitable applications. The facilitator decides whether both views are needed and explains that this exercise's synthetic suitability rule is only a teaching device.

**Check it.** Open `results/precomputed/baseline_audit_gender.json`; each row reports group `count`, `selection_rate`, and `recall` when labels are complete. The gender population totals 481 women, 464 men, and 15 nonbinary applications across the 8 vacancies.

**Takeaway:** A rate is only meaningful when its population and question are clear.

## 2. A score penalty shifts the cutoff (20 min)

**Do the obvious thing.** Compare the qualification baseline with the simulated historical score, which adds group penalties and access-proxy bonuses before taking the top five.

**See the problem.** Across 8 vacancies, the mean gender selection-rate change is −1.86 percentage points for women (481 applications) and +1.97 points for men (464 applications). The score components are deliberately fabricated, visible columns—not a hidden historical discovery.

**PAUSE — 3 min:** If a model changes the names at ranks 4–6, what would you ask before calling the group-rate change meaningful?

**The fix and the human decision.** Read `gender_score_effect`, the other three group-effect columns, and both proxy effects before interpreting outcomes. The facilitator chooses which job-related criteria are defensible and whether a real process has enough independent evidence to investigate.

**Check it.** Compare `results/precomputed/comparison_gender.json` with `qualification_baseline_run.json` and `biased_historical_run.json`. The report pairs identical candidate IDs, vacancies, labels, and cutoff size; only the scoring recipe changes.

**Takeaway:** A metric can detect a controlled change without explaining or judging a real-world disparity.

## 3. Equal suitability labels still leave people out (20 min)

**Do the obvious thing.** Look only at top-five selection rates.

**See the problem.** The synthetic rule calls an application suitable when skill match is at least 62, relevant experience is at least 3 years, and the required certificate is present. The simulated score lowers average gender recall by 6.24 points for women and raises it by 6.76 points for men across the 8 vacancies.

**PAUSE — 3 min:** Would you prefer a short list with similar selection rates or one that misses fewer suitable people? What evidence would help make that choice?

**The fix and the human decision.** Inspect both selection rate and recall, then ask a recruiter to validate the suitability rule against job requirements. Fairlearn does not choose a fairness definition or acceptable trade-off.

**Check it.** `comparison_gender.json` includes per-vacancy `recall_change`; the saved judgment file has 960 labels, generated independently of the four group fields but still not human-validated.

**Takeaway:** Balanced access and missed-qualified-candidate questions measure different outcomes.

## 4. Tiny groups make large claims fragile (20 min)

**Do the obvious thing.** Read every group rate as if it were equally precise.

**See the problem.** There are 15 nonbinary applications across 8 vacancies, fewer than 2 per vacancy on average; some vacancy-level groups contain zero suitable cases, so recall is undefined. The audit flags groups below 5, but the flag is not a statistical test.

**PAUSE — 3 min:** What should a team report when a group's cell is too small to support a stable comparison?

**The fix and the human decision.** Show counts next to rates, retain `null` where a metric has no denominator, and agree a privacy-safe reporting or collection approach with the responsible people. Do not infer or merge identities just to make a larger count.

**Check it.** Open `results/precomputed/biased_audit_gender.json`; inspect `count`, `sufficient_sample`, and nullable `recall` for each vacancy and group.

**Takeaway:** A small-sample warning describes evidence limits; it cannot repair them.

## 5. Four separate audits are not an intersectional audit (20 min)

**Do the obvious thing.** Read the four marginal comparisons: gender, ethnicity, economic class, and geography.

**See the problem.** The reports contain 8 vacancy comparisons for each of the 4 dimensions, but they do not report joint groups such as rural women in a particular class. The separate margins can hide a concentrated gap.

**PAUSE — 3 min:** Which intersection would you examine first, and how would you protect people represented by small cells?

**The fix and the human decision.** Plan a privacy-reviewed, adequately supported intersectional audit with purpose-limited data and independent suitability judgments. The facilitator should state that these fabricated categories and this cohort are not a proxy for real protected-group data.

**Check it.** Compare the four files `results/precomputed/comparison_*.json`. Each reports one dimension at a time; there is no combined-group result in this exercise.

**Takeaway:** Passing separate group checks does not establish fairness for people at group intersections.

## 6. A passing data check does not validate the decision (15 min)

**Do the obvious thing.** Treat a complete audit file and successful Fairlearn calculation as evidence that the evaluation is sound.

**See the problem.** All 960 judgments come from a deterministic rule. No recruiter reviewed them, and the saved comparison does not estimate uncertainty or test real hiring outcomes.

**PAUSE — 3 min:** What evidence would you require before using this workflow on real shortlisting decisions?

**The fix and the human decision.** Specify data provenance, an approved collection purpose for sensitive audit attributes, independent reviewer guidance, minimum reporting counts, uncertainty analysis, and a human escalation path. A responsible hiring team must decide those controls.

**Check it.** Read `data/SOURCES.md`, the generator's seed/recipe in `synthetic_hr_demo/metadata.json`, and `evaluate.py`'s validation and metric implementation. Confirm that the reports label the run synthetic and preserve counts.

**Takeaway:** Passing input checks does not prove a model works or that its outcomes are fair.

## Run the audit yourself

Recreate the gender report from the committed synthetic inputs:

```text
uv run --no-sync --python 3.12 python 04-fairlearn/evaluate.py compare-synthetic --baseline 04-fairlearn/synthetic_hr_demo/qualification_baseline_run.json --biased 04-fairlearn/synthetic_hr_demo/biased_historical_run.json --groups 04-fairlearn/synthetic_hr_demo/audit_groups_gender.csv --judgments 04-fairlearn/synthetic_hr_demo/synthetic_suitability_judgments.csv --output results/gender/comparison.json
```

The command also writes `results/gender/baseline_audit.json` and `results/gender/biased_audit.json`. To regenerate all four dimensions, run the same command four times and change `gender` to `ethnicity`, `economic_class`, and `geography` in the group file and output path. For each dimension's filenames, use `audit_groups_<dimension>.csv`.
