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

## Problem 3 — Can historical decisions introduce bias? (25 minutes)

### Learning objectives

Find group differences in synthetic historical shortlisting, compare within qualification bands, and distinguish shortlist, hire, and observed performance.

### Facilitation

Before the notebook reveals history, ask: “Is a prior rejection a reliable label for lack of qualification?” Then have participants calculate group rates and examine qualification bands. Ask them to identify the denominator before interpreting a rate.

**Expected output for JD-01, from the fixed seed:** 50 applications; 19 males and 31 females. Historical shortlisting is 7/19 (36.8%) for males and 3/31 (9.7%) for females. The qualification bands show differences also within the middle and upper score bands. Geography is 7/28 (25.0%) for Addis Ababa and 3/22 (13.6%) outside Addis Ababa. These small synthetic comparisons reveal the planted mechanism; they are not external evidence.

There are 10 historically shortlisted applicants: 5 hired and 5 not hired. The other 40 have no hiring decision because they were not shortlisted. Post-hire performance is observed for 5 hires; 45 values are missing. The notebook keeps missing values blank.

**Explain after discovery:** the fixed-seed generator assigns sex and geography independently of the constructed qualification signal, then adds group boosts to the simulated historical decision score. Facilitator-only design disclosure: +9 points for the Male group, +7 for Addis Ababa, with random noise; top 10 shortlisted, top 5 of those hired. See `data/generate_history.py`.

**Common misconceptions:** “No hire means poor performance”; “similar qualification scores prove discrimination”; “the difference is an effect estimate.” Clarify that hiring outcomes are not observed for non-shortlisted people, group differences flag a question, and this controlled synthetic mechanism is known by design.

**Discuss:** What independent assessment could cover candidates excluded earlier? What would a prospective audit need to record?

**Key takeaway:** historical labels encode past decisions and selective observation; they are not neutral ground truth.

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
