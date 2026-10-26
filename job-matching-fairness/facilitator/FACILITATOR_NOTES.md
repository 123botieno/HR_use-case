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

## Problem 3 - Can historical decisions change who gets shortlisted now? (25 minutes)

### Learning objectives

- Separate application, shortlisting, hiring, and observed performance.
- See a model learn a deliberately biased pattern from past shortlist labels and apply it to a held-out job.
- Compare model recommendations with a qualification-score-only proxy and the historical shortlist.
- Distinguish agreement with history from evidence of candidate suitability.

### Facilitation

Start with the funnel question: if 100 apply, 10 are shortlisted, and one is hired, are the other 90 negatives? Establish that they were not shortlisted and have no observed hiring or performance outcome. The 9 shortlisted but not hired have an observed hire decision; they still have no post-hire performance outcome.

At the PAUSE, ask pairs to predict what the history-trained model will do on JD-01. Explain the design only after predictions: the logistic model is trained on the other 13 synthetic jobs and then used to rank the 50 JD-01 applicants. For this risk exercise only, its inputs include the simulated qualification score, sex group, and geography group. Thus it can learn the generator's explicit group preference. The protected attributes are intentionally included here to make the risk visible; TF-IDF, BM25, and LLM text ranking do not receive them.

**Expected output for JD-01, fixed seed:**

| Current shortlist rule | Male selected | Female selected | Top-10 overlap |
|---|---:|---:|---:|
| Qualification-score-only proxy | 5/19 (26.3%) | 5/31 (16.1%) | 7 with historical |
| Historical shortlist replay | 7/19 (36.8%) | 3/31 (9.7%) | 10 with history by design |
| Logistic model trained on history | 10/19 (52.6%) | 0/31 (0%) | 4 with historical; 1 with proxy |

The model was fit on 13 jobs; JD-01 is held out from fitting. The learned weights are +0.075 for the qualification proxy, +2.926 for the Male indicator, and +1.948 for the Addis Ababa indicator. Positive group weights show association with historical shortlist labels in this generated dataset, not a causal effect. Its held-out shortlist-label metrics are 76% accuracy, 40% precision, and 40% recall. An always-not-shortlisted baseline gets 80% accuracy because 40/50 records have a negative historical shortlist label. The score-only Top 10 gets 88% accuracy, 70% precision, and 70% recall against the same history. Emphasize that all of these scores measure agreement with synthetic, biased shortlist labels, not correct suitability. The 80% baseline also illustrates why accuracy alone can mislead with imbalanced labels.

**How to evaluate whether the demonstration code is working:** check that JD-01 is excluded from model fitting; each Top-10 rule produces exactly 10 candidates; the replay matches 10/10 historical labels by construction; and the model's held-out confusion counts are TP=4, FP=6, FN=6, TN=34. Check candidate overlaps and selected/applicant counts by group. These checks validate the split and calculations, not the fairness or quality of hiring decisions.

**Hiring funnel output:** 50 applications -> 10 historically shortlisted -> 5 hired -> post-hire performance observed for 5. Forty applicants have no hiring decision; five shortlisted applicants were not hired; 45 performance values are missing. Historical hires are 3/19 males and 2/31 females overall; among shortlisted candidates, 3/7 males and 2/3 females were hired. These conditional groups are very small. The 40 missing hire decisions and missing performance values are unknown outcomes, not negatives.

**What this does and does not demonstrate:** it directly demonstrates a model learning a designed group preference from past shortlist labels when the group attributes are available as inputs. It does not establish that real data would produce the same effect, and it does not train or change the three text matchers. In a real evaluation, historical hire labels are selective and shortlist labels can be biased. Seek independent job-related assessments that cover people not advanced, evaluate on a genuinely separate cohort, and track outcomes prospectively. Historical agreement alone measures imitation.

**Common misconceptions:** "The 90 not shortlisted are hiring negatives"; "the highest simulated score is objectively best"; "held-out accuracy proves the model works"; "the synthetic disparity estimates real hiring." Correct each: no downstream label for the 90; the proxy score is not ground truth; the model is evaluated against biased history; all values are synthetic and small.

**Discuss:** What independent assessment could cover candidates excluded earlier? What would make an outcome label defensible? How would a prospective audit catch a harmful shift before relying on the model?

**Key takeaway:** a model trained on historical shortlist labels can carry a designed group preference into a new shortlist; agreement with those labels does not establish that it selects suitable people.

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
