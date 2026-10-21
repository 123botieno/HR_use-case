# 07 — Job matching: three independent methods

## Purpose

Compare [LLM](llm/README.md), [BM25](bm25/README.md), and [TF-IDF](tfidf/README.md) on identical candidate pools, returning five candidates per JD from each method.

## Shared inputs

Vacancy ID, confirmed JD text and requirements, candidate IDs and matching text, source references, dataset version, and shortlist size fixed at five.

## Shared output contract

Each ranking record will include run ID, vacancy ID, candidate ID, algorithm, algorithm/configuration version, raw score, rank, shortlist membership, evidence/artifact references, and review flags. LLM evidence must identify the source passage; lexical methods may report term contributions without claiming requirement verification.

Sort descending by score, breaking exact ties by ascending candidate ID. Keep all rankings, flag ties at rank five, and record extraction exclusions. Return fewer than five only when fewer than five candidates can be assessed, with an explicit reason.

Do not blend the methods or choose a winning method before [evaluation](comparison/README.md). Top-five membership does not itself establish qualification.

## Setup and use

Run from the project root after preparing data:

```powershell
python 07-job-matching/run.py --methods bm25 tfidf
```

For all three methods, configure the workshop's shared OpenRouter key and a confirmed rubric, then run `python 07-job-matching/run.py --rubric data/rubric.json`. The workflow lives in [run.py](run.py), with algorithm implementations in [BM25](bm25/score.py), [TF-IDF](tfidf/score.py), and [LLM](llm/score.py). Top-five ranking logic is in [shortlist.py](shortlist.py); comparison metrics are in [comparison/evaluate.py](comparison/evaluate.py).

The default candidate pool follows source vacancy associations; `--pool-scope all` scores every prepared CV against each selected JD. Use `--jd JD-01` to select a vacancy. See [the running guide](../docs/RUNNING.md) for output details.

## Model settings and evaluation

The [BM25](bm25/README.md) and [TF-IDF](tfidf/README.md) lessons explain their scoring settings and how to test alternatives. Current settings are fixed in code; the runner does not automatically tune hyperparameters. Use development vacancies and independent recruiter judgments to compare alternatives, then freeze settings before held-out evaluation. [The comparison lesson](comparison/README.md) explains supported metrics and missing-label behavior.

The MLOps lessons from [DVC](../01-dvc/README.md) through [Prefect](../06-prefect/README.md) share a teaching structure: where each tool fits, the flow it runs, discrepancies it can reveal, discussion prompts, and current limits. They distinguish implemented behavior from planned work.

## How we compare the three methods

BM25, TF-IDF, and LLM each rank the same candidate pool independently for each JD. We do not blend scores because they have different meanings and scales. We first compare shortlist overlap and runtime; we can compare ranking quality only after independent recruiter judgments are supplied. The evaluator reports Precision@5, Recall@5, and NDCG@5 only when the relevant labels are sufficiently complete. See [the comparison guide](comparison/README.md) for formulas, label requirements, and interpretation.

### How tied scores enter the top five

The ranker sorts by descending score and breaks equal-score ties by ascending candidate ID. It selects ranks one through five. When the last selected and first excluded scores tie, the boundary tie is flagged in `rankings.csv` and `run.json`, while the output still contains five candidates. Candidate ID makes the result reproducible; it does not establish merit. Prior local experiments recorded LLM cutoff ties; those reports are not committed. Recreate a run and review its boundary ties rather than interpreting the last candidate as clearly stronger.

## Outputs and evidence gaps

Every run writes `run.json`, `rankings.csv`, `shortlists.csv`, `comparison_shortlists.csv`, `report.md`, `comparison.json`, and `judgments_template.csv`. The [running guide](../docs/RUNNING.md) describes each artifact; the [comparison guide](comparison/README.md) explains which metrics need independent judgments.

The source archive has documented missing and unreadable files; inspect `data/prepared/inventory_issues.json` after restoring and preparing it. Independent recruiter judgments have not been supplied, so top-five lists are experimental relevance/evidence rankings, not verified suitable-candidate recommendations; the run cannot establish which method performs best. Synthetic fit tiers, mock group labels, and mock suitability labels are not substitutes for recruiter judgments. Earlier run artifacts are local and excluded from Git.

## Code walkthrough: one matching run

1. The command line enters `jobmatch.cli.main()`, which dispatches `run` to `execute()` in [run.py](run.py).
2. `execute()` checks method names, pool scope, and LLM worker count; loads the dataset; runs mandatory dataset validation and optional GX; then selects requested JDs.
3. For each JD it creates a sorted candidate pool and hashes candidate IDs plus text hashes. Each requested method receives that same pool.
4. The method scorer returns one score and evidence record per candidate plus its configuration. BM25 and TF-IDF are local; LLM uses the configured API and rubric.
5. `rank()` combines IDs, scores, and evidence; sorts descending with candidate ID tie-breaking; assigns ranks, top-five flags, and cutoff/uninformative flags.
6. `validate_rankings()` checks pool coverage and ranking invariants. Errors are caught per JD-method pair and saved as explicit failures; the method is not replaced by another.
7. The runner saves `run.json` during and after execution. It then writes ranking/shortlist CSVs, side-by-side shortlist CSV, full-pool blind judgment template, `comparison.json`, and `report.md`.
8. `comparison.json` initially has only metrics supported without recruiter labels. Add reviewed judgments and rerun the evaluator to calculate suitable-candidate quality metrics.

This sequence is the shared path used by the individual scorer scripts and the Prefect flow. See each method README for its scoring internals.

