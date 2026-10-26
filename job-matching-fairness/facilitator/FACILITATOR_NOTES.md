# Facilitator Notes — Job Matching and Fairlearn Workshop

## Workshop at a glance

**Duration:** 2 hours. **Format:** pairs, one facilitator. **Materials:** executed `job_matching_fairness.ipynb`, this guide, and the slide deck. **Kernel:** Python 3.12 using the repository lock. No API key is needed in cached mode.

### Before participants arrive

1. Follow the install steps in the workshop README and open the notebook.
2. Confirm the kernel and run all cells. Keep `JOB_ID = 'JD-01'` for the shared debrief.
3. Put the slides in presenter mode. Ask pairs to keep a prediction sheet with columns: prediction, evidence, interpretation, limitation.
4. Establish that all profiles and history are synthetic. Do not represent results as facts about real Ethiopian applicants or employers.
5. If the notebook cannot run, use its saved outputs and discuss the prompts. The LLM cache is prior project output, Top 5 only, and not a live call.

## Timing and facilitation map

| Time | Episode | Purpose |
|---|---|---|
| 00:00–00:08 | Welcome and setup | Set the decision context and evidence boundary. |
| 00:08–00:28 | Problem 1 | Compare ranking methods and candidate overlap. |
| 00:28–00:48 | Problem 2 | Change settings and inspect ranking stability. |
| 00:48–01:13 | Problem 3 | Discover group-skewed history and selective labels. |
| 01:13–01:48 | Problem 4 | Use Fairlearn for selection differences; discuss limits. |
| 01:48–02:00 | Problem 5 | Make and defend a bounded recommendation. |

## Opening — 8 minutes

**Say:** “A shortlist determines who gets more attention. Today we will compare ways to rank the same candidate pool, then ask what group differences and incomplete outcomes let us conclude.”

**Ask:** “What evidence would you want before allowing a ranking to affect a person’s application?” Take two or three answers. Do not preview the synthetic bias mechanism.

**Expected output:** participants name job-related criteria, review, and evidence about outcomes. Clarify that no single score can establish qualification.

**Fallback:** if setup takes more than five minutes, switch to saved notebook outputs and do the exercise verbally; protect time for Problems 3–5.

## Problem 1 — Do methods recommend the same candidates? (20 minutes)

### Learning objectives

Distinguish term-weighted retrieval, BM25 retrieval, and requirement-evidence LLM scoring; compare ranks without treating scores as commensurate.

### Facilitation

Ask participants to read the JD preview and candidate CV preview. Give three minutes to write predictions. Have pairs run the cells and circle overlaps in the Top-5 table.

**Expected output:** complete TF-IDF and BM25 rankings of 50 CVs; cached LLM Top 5; an overlap table and rank plot. On the committed seed, TF-IDF and cached LLM share 1 of their top 5; BM25 shares 0 with TF-IDF and 0 with cached LLM. These are run outputs, not relevance judgments.

**Interpretation:** TF-IDF emphasizes distinctive terms across the CV pool. BM25 increases scores for repeated query terms with saturation and length normalization. The LLM output is a saved prior run's evidence-weighted ranking. Different candidate pools, wording, tie-breaking, and rubric choices can change ranks.

**Common misconception:** “The largest score is best.” Scores belong to different methods; compare ranks and overlap. A lexical match can reward repeated wording; an LLM score can reflect rubric and model choices.

**Discuss:** Which candidate changed most? What evidence would you inspect? What blinded, job-related judgments would support a relevance claim?

**Key takeaway:** ranking methods implement different notions of text relevance; overlap is not correctness.

## Problem 2 — How do settings affect the ranking? (20 minutes)

### Learning objectives

Run controlled parameter changes and separate rank movement from improved matching quality.

### Facilitation

Ask each pair to choose one change and predict its effect. Keep all other inputs fixed. Let them run the default and changed TF-IDF/BM25 settings; ask what moved before showing the next example.

**Expected output:** side-by-side rank positions for the top candidates and Top-K overlap at K=3, 5, and 10. The exact output is saved in the notebook. There is no universally best `ngram_range`, `max_features`, `k1`, or `b` without independent relevance evidence.

**LLM prompt/rubric exercise:** `LLM_RUBRIC`, `SCORING_PROMPT`, `LLM_MODEL`, and `LLM_TEMPERATURE` are visible in the optional live cell. Changing them has no effect in cached mode. Live mode requires the shared OpenRouter key, uses only workshop CV text, and calls the existing project scorer. The existing scorer's default path omits temperature; the wrapper allows temperature on a customized request, subject to model support.

**Common misconception:** “Stable ranks mean the ranking is valid.” Stability only says a setting change did not move candidates much; it does not say the result matches job needs.

**Discuss:** Which setting moved the most candidates? What separate relevance measure could decide whether that change helps?

**Key takeaway:** parameter choices change who is surfaced; their value requires job-related evaluation.

## Problem 3 - What do historical hiring records tell us? (25 minutes)

### Learning objectives

- Separate the shortlisting decision, the hiring decision, and post-hire performance.
- Identify which historical labels are observed and which outcomes are unknown.
- Discuss how past decisions could shape current criteria, models, or evaluations without claiming that the current text matchers learned from this dataset.
- Propose a sensible evaluation that does not treat missing outcomes as negatives.

### Facilitation

Open with the participant's 100 / 10 / 1 scenario: 100 apply, 10 are shortlisted, and one is hired. Ask participants to write labels separately for shortlisting, hiring, and performance before showing the explanation.

**Expected interpretation:** for the shortlisting decision, 10 are positive and 90 are not shortlisted. Those 90 are negatives only for that recorded shortlisting decision; they are not proven unqualified. For hiring across all applicants, one is hired, nine shortlisted applicants are not hired, and 90 who were never shortlisted have no observed hire decision. Therefore this is not 99 negatives and one positive. The number hired does not itself tell us the person's job performance; if performance is recorded only for hires, at most one result is observed and the other 99 are missing.

Then inspect the committed synthetic data. For JD-01, 50 applications lead to 10 historical shortlists and 5 hires; post-hire performance is recorded for those 5 hires. Forty applicants have no hiring decision, five shortlisted applicants were not hired, and 45 performance values are blank. Historical shortlisting is 7/19 males (36.8%) and 3/31 females (9.7%), and 7/28 Addis Ababa applicants (25.0%) versus 3/22 outside Addis Ababa (13.6%). These are intentionally simulated results.

**Discuss how history might affect current hiring:** if prior shortlist or hire labels are treated as evidence of who is qualified, a future rule or model may reward applicants who received past access and treat those excluded as poor examples. If the same labels are used to evaluate a new system, high agreement can mean it imitates the old process, including its bias. The three text rankers in this workshop do not train on these history labels; this discussion is about a possible pathway, not a demonstrated causal effect in those rankers.

**How to evaluate a current process:**

1. Measure stage-by-stage selection rates for each group using the applicants eligible at that stage as the denominator. Problem 4 uses Fairlearn for current algorithm selection rates.
2. Report label coverage: the shortlist decision is known for everyone, hiring is known only for shortlisted candidates, and performance is observed only for hires.
3. Treat comparison with historical decisions as agreement, not correctness. Do not score the 90 unknown hiring outcomes as negative.
4. For job-related validity, collect an independent structured assessment, such as a consistent work sample, for applicants across groups. Employee performance can only be observed after hiring, so it cannot tell us how rejected applicants would have performed.
5. Follow a prospective process and review both decisions and missingness before making claims about impact.

**How to tell the analysis is wired correctly:** verify the 100 / 10 / 1 counts in the example; for the synthetic JD-01 data, verify 50 / 10 / 5 and the 40 missing hire decisions / 45 missing performance values. Check group-rate numerators and denominators. These checks confirm the counts and definitions, not that the historical decisions were good decisions.

**Common misconceptions:** "the 90 not shortlisted are hiring negatives"; "not hired means poor performance"; "historical agreement proves the new system works"; "the synthetic group rates describe real hiring." Correct each by naming the decision target, keeping unobserved outcomes missing, and distinguishing agreement from independent validation.

**Discuss:** Which old decisions could influence a new process? What independent job-related evidence could assess applicants the old process excluded? How would you report a current system's group rates and its unknown outcomes?

**Key takeaway:** historical records show what the process decided, not what excluded applicants would have done; missing labels need to stay unknown.

## Problem 4 — Are the algorithms fair? (35 minutes)

### Learning objectives

Use Fairlearn `MetricFrame` to measure selection rates, demographic parity difference and ratio within one job; interpret group counts and label limits.

### Facilitation

Ask pairs to predict which method will show the smallest gap and whether that means it is best. Run the sex audit, then the geography audit. Point to the `n` beside every rate. Have pairs change K for lexical methods and explain why cached LLM is fixed at K=5.

**Expected output for JD-01, K=5, sex groups:** TF-IDF selects 2/19 males and 3/31 females (selection rates 10.5% and 9.7%, demographic parity difference 0.0085, ratio 0.919). BM25 selects 3/19 males and 2/31 females (15.8% and 6.5%, difference 0.0934, ratio 0.409). Cached LLM selects 2/19 males and 3/31 females (same rates as TF-IDF). These figures are per-job synthetic results; ratios can be unstable with small groups.

**Explain the matching counts:** the TF-IDF and cached LLM methods happen to have the same 2-man/3-woman composition, but their Top-5 lists share only one candidate. BM25 has a 3/2 split. The methods rank text and do not receive the synthetic sex field. With only five shortlist places, equal group counts can happen even when candidate rankings differ; a matching split does not show equivalent rankings or prove fairness. Emphasize the denominators (19 males, 31 females), since the same selected counts need not yield the same rates.

**Scope boundary:** the biased mechanism is in the synthetic historical shortlist labels. The three matching methods are not trained on those labels in this workshop. Participants compare their selections with historical decisions as an example of how a biased label can shape evaluation; agreement is not correctness.

**Label discussion:** Fairlearn can calculate group-specific precision/recall/error rates and equalized odds when valid reference labels cover the relevant applicant pool. Here, historical shortlist agreement is shown as *agreement only*. The observed hire field is blank for non-shortlisted applicants and post-hire performance exists only for hires. Do not call either label a complete correctness target; do not calculate equalized odds from biased historical labels.

**Expected output for historical agreement:** agreement with historical shortlist differs by group and method. This is agreement with a prior decision process, not candidate correctness or performance.

**Common misconceptions:** “Parity proves fairness”; “any gap proves discrimination”; “choose the lowest gap”; “a ratio of zero means the system is entirely unfair.” Explain context, counts, consequences, and alternative criteria. A zero ratio can occur when a group has no selected applicant at a very small K.

**Discuss:** Which discrepancy deserves investigation? What evidence and human decision would follow? How does changing K move rates?

**Key takeaway:** Fairlearn measures defined group differences; people decide what they mean and what action is justified.

## Problem 5 — Which approach should advance? (12 minutes)

### Learning objectives

Make a recommendation that separates observed evidence, assumptions, and unresolved questions.

### Facilitation

Give pairs five minutes to complete the decision table and five minutes for two groups to report. Ask them to choose advance, revise and re-evaluate, or do not advance. Require one support, one limitation, and one next evidence source.

**Expected answer:** any of the three decisions can be defensible if bounded by evidence. A strong answer avoids declaring a universally fairest algorithm, notes the LLM cache only covers K=5, says historical agreement is not correctness, and identifies independent job-related review and broader outcome collection as prerequisites for a real evaluation.

**Common misconception:** “The smallest DP gap wins.” A low gap may coexist with poor matching, and parity alone does not establish fairness or job validity.

**Discussion questions:** Who owns independent evaluation? What would justify a live LLM run? What action follows a concerning gap?

**Key takeaway:** choose the next evidence-gathering step, not a winner unsupported by the data.

## Answers and evidence inventory

- Source data: 14 available JDs and 699 readable fictional CVs. JD-13 and one unreadable JD-15 CV were unavailable in the source bundle; these omissions and their effect are documented in `data/SOURCES.md`.
- Synthetic history: 699 applicant-job rows. Per complete 50-CV job: 10 shortlisted, 5 hired; post-hire performance observed for the 5 hires only.
- Cached LLM: existing repository `comparison_shortlists.csv` top-five records for 14 JDs; K=5 only, explicitly offline and not live inference.
- For exact current outputs, use the executed notebook. If helper/data changes, rerun the notebook before teaching and replace these figures from its outputs.

## Discussion questions for the close

- What is the target decision, and who bears the cost of each error?
- What evidence could assess people who were historically excluded?
- Which audit attributes are necessary, restricted, and kept out of scoring?
- What sample size and uncertainty evidence should accompany a disparity?
- Who has authority to stop a process or request a new review?
