# Optional exercises

All exercises use fictional records. None produces evidence about real hiring.

1. **Change the bias recipe.** In `synthetic_hr.py`, set one gender penalty to zero and regenerate with a new output directory and fixed seed. Compare selection-rate and recall changes; explain which effects remain through correlated proxies.
2. **Change the shortlist size.** Change `_ranking()`'s cutoff from five to three or ten, regenerate, and compare how discrete selection-rate changes behave. Keep the before/after cutoff explicit.
3. **Leave labels incomplete.** Remove one judgment row from a copy of the judgments CSV, audit it, and explain why the report omits recall rather than treating missing labels as unsuitable.
4. **Add an intersection carefully.** Create an experimental joint label from two synthetic dimensions, print cell counts first, and decide whether any cell is too small to report. Do not merge identities to inflate counts.
5. **Write a real-audit plan.** Specify the data owner, purpose and collection basis, access controls, independent suitability review, uncertainty method, escalation owner, and conditions for pausing use.
