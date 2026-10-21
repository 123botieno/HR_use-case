# Intro slides: HR shortlist fairness (10–15 min)

Six-slide content for transfer to the workshop's shared template. The template was not included in this checkout.

## 1. Setting

A fictional hiring team uses a ranked shortlist to decide who receives further review. A model trained on old decisions can repeat past patterns, while the team can observe later hiring outcomes only for people who reached the shortlist.

## 2. The decision and the cost of mistakes

Who receives shortlist review? Excluding a suitable candidate can deny them consideration; including a weak match can displace another applicant. A ranking score does not establish qualification or predict job success.

## 3. The data

The fixed-seed demonstration contains 8 fictional vacancies and 960 applications. It uses mock gender, ethnicity, economic-class, and geography fields; visible score penalties; access-proxy bonuses; and an explicitly incomplete `historical_hired` outcome.

## 4. The missing outcomes

Only the 40 historically shortlisted applicants have observed hire outcomes. The other 920 outcomes are missing, not “not hired.” A separate synthetic suitability label exists only to demonstrate recall calculations and is not an observed hiring result.

## 5. Objectives

Participants will trace bias in historical decisions, identify selective outcome observation, read group selection rates and label-dependent recall, and name evidence gaps that prevent conclusions about real applicants.

## 6. What participants will do

Four episodes: inspect historical score effects; diagnose missing outcomes; compare group access at the top-five cutoff; and decide what independent evidence is needed to assess missed suitable candidates. Saved reports support discussion without rerunning code.
