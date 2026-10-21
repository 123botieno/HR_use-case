# Intro slides: HR shortlist fairness (10–15 min)

**Template note:** This is six-slide source content in Markdown. No shared slide template was present in the workspace; transfer the content to the workshop's presentation template when available.

## 1. Setting

One vacancy receives a ranked list of candidates and a five-person recommended shortlist. A recruiter owns the final decision; the model score is evidence of fit to stated criteria, not hiring probability.

## 2. The decision and the cost of mistakes

Who reaches the shortlist, and who is left out? A false exclusion can remove a suitable candidate from review; an unsupported inclusion can displace another candidate. The system must show evidence and missing information so a person can review it.

## 3. The teaching data

The fixed-seed demonstration has 8 fictional vacancies and 960 fictional applications. It assigns mock gender, ethnicity, economic-class, and geography groups; it injects explicit score penalties and access-proxy bonuses. Every identity, score, label, and decision is simulated.

## 4. What Fairlearn measures

`MetricFrame` reports per-group selection rate for each vacancy. With complete synthetic suitability labels, it also reports recall. The audit shows counts and small-sample flags; it does not calculate confidence intervals or decide what disparity is acceptable.

## 5. Objectives

Participants will trace where a synthetic penalty enters, compare baseline and biased shortlists, interpret selection rate and recall, and identify limits from small groups, labels, and separate group dimensions.

## 6. What participants will do

Six lab episodes: choose a denominator; inspect a changed cutoff; compare suitable-candidate recall; assess small-group evidence; identify missing intersections; and state what a real audit would need. All episodes have saved outputs, so discussion can proceed without running the code.
