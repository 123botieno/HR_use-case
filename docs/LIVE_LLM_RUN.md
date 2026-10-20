# Live OpenAI comparison run

Completed on 15 October 2026 using the OpenAI model configured locally in .env. The run is experimental: the source-derived JD rubrics remain unconfirmed.

## Outputs

- [Human-readable three-method shortlist report](../runs/20261015T101453Z-402c9b11/report.md)
- [Side-by-side shortlists CSV](../runs/20261015T101453Z-402c9b11/comparison_shortlists.csv)
- [All shortlist entries CSV](../runs/20261015T101453Z-402c9b11/shortlists.csv)
- [Full run, configurations, rankings, and evidence](../runs/20261015T101453Z-402c9b11/run.json)
- [Comparison and overlap results](../runs/20261015T101453Z-402c9b11/comparison.json)
- [Output verification](../runs/20261015T101453Z-402c9b11/verification.json)
- [Blank independent-review template](../runs/20261015T101453Z-402c9b11/judgments_template.csv)

## Verified results

The run completed all 42 JD/method combinations: 14 JDs multiplied by LLM, BM25, and TF-IDF. Every shortlist contains five unique candidates, giving 210 entries overall and 70 LLM shortlist entries. The LLM assessed all 699 available CVs in their source-associated vacancy pools. All 2,756 accepted supported/explicitly-not-met evidence citations were checked against literal CV source passages.

An initial pass exposed incorrect citations and evidence statuses. Corrective retries and deterministic literal-source citation resolution were added and tested. The successful run reused validated cached responses and completed without unresolved failures. Original rubric confirmation flags were preserved.

## Interpretation

These are experimental relevance/evidence rankings, not verified qualification or hiring decisions. Independent recruiter judgments have not been supplied, so Precision@5, Recall@5, and NDCG@5 remain unavailable. Shortlist overlap is available but does not identify the most accurate algorithm.

Runtime includes cache reuse and should not be treated as a cold-run latency benchmark. Actual API billing is not available from these reports; usage records do not recover invalid responses discarded by the initial implementation.

JD-13 and its 50 CVs remain missing, and CV-15-035 remains unreadable. The source files were not changed. Generated run artifacts are excluded from Git and remain in the local workspace.
