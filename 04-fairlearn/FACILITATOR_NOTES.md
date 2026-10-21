# Facilitator notes (2 hours)

**Roles:** one facilitator; participants work in pairs. **Room setup:** repository root open, CPU laptop, no network or API key needed. Keep the six lab episodes on screen; use the PAUSE prompts verbatim and let participants write before discussion.

| Clock | Lead and say | Ask / PAUSE | Expected output | Fallback if it fails |
|---|---|---|---|---|
| 00:00–00:10 | Facilitator: “These are fabricated records and outcomes. We are testing whether the audit detects a shock we put into the scoring rule.” Show README and provenance. | What would make an HR fairness result trustworthy? | Participants distinguish a demonstration from evidence about real applicants. | If setup is incomplete, use the saved reports; no install is needed to discuss them. |
| 00:10–00:25 | Participants inspect Episode 1; facilitator explains selection-rate and recall denominators. | **PAUSE 1:** Which applicant set belongs in each denominator? | Counts/rates in the baseline report; a denominator proposal. | Open `results/precomputed/baseline_audit_gender.json`. |
| 00:25–00:45 | Pairs compare baseline and biased gender outcomes. Point to explicit penalty/proxy columns. | **PAUSE 2:** What would you inspect before attributing a cutoff change? | They identify fixed candidates, vacancy, labels, top-five cutoff; scoring changes. | Use `comparison_gender.json` and the CSV score-effect columns. |
| 00:45–01:05 | Facilitator introduces synthetic suitability rule. Participants compare rate and recall. | **PAUSE 3:** Which outcome matters for this decision, and what evidence is missing? | Two distinct outcome definitions; recognition labels are unvalidated. | Read the gender comparison's `recall_change` values. |
| 01:05–01:25 | Participants review the nonbinary counts and null recalls. | **PAUSE 4:** What do you report when cells are small? | Counts beside rates; no invented/merged groups; note privacy. | Open the saved biased gender audit; explain `sufficient_sample` and null. |
| 01:25–01:45 | Groups compare the four marginal audits and name an intersection they would investigate. | **PAUSE 5:** Which joint group is currently invisible? | A proposed intersection and a privacy concern. | Show the four comparison files; emphasize there is no joint table. |
| 01:45–02:00 | Facilitator closes with data quality, independent judgments, and human review. | **PAUSE 6:** What must be true before this could inform a real process? | A list of evidence/controls and an accountable human decision owner. | Read source notes and limits; invite written take-home answers. |

## Discussion prompts

- Who chooses the fairness measure and acceptable threshold for this hiring context?
- How could CV readability, missing evidence, vacancy requirements, or pool composition create another gap?
- How should audit attributes be collected, access-controlled, retained, and excluded from scoring?
- Which additional evidence would separate score effects from suitability-label or data-quality effects?
- What action should follow a detected gap, and who can pause use of the shortlist?

## Verified figures to keep visible

- Cohort: 8 fictional vacancies × 120 applications = 960, seed `20261020`.
- Gender counts: 481 women, 464 men, 15 nonbinary across all vacancies.
- Mean gender selection-rate change: women −1.86 percentage points; men +1.97 points.
- Mean gender recall change: women −6.24 points; men +6.76 points.

These averages summarize eight vacancy-level reports. The labels and shock are simulated; no inferential uncertainty is estimated. Counts and full precision appear in `results/precomputed/`.
