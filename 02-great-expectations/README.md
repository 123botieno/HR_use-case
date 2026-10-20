# 02 — Great Expectations: stop bad inputs and rankings at the gate

## Where this fits

Validation runs before scoring and again on each produced ranking. The project combines mandatory Python checks with an optional Great Expectations (GX) suite. These checks catch malformed or inconsistent artifacts; they do not establish that a CV is truthful, a rubric is job-related, or a ranking is fair.

## Flow

1. Load the prepared dataset and verify its dataset and text hashes.
2. Check jobs and candidates exist, IDs are unique, text and source sections are present, and candidate rows refer to valid jobs with nonempty pools.
3. Optionally run an ephemeral GX suite on candidate rows.
4. After each method scores a vacancy, check the ranking covers exactly the shared pool, IDs are unique, scores are finite, ranks are consecutive, ordering follows score and tie rules, and shortlist membership agrees with ranks.
5. Stop the affected method or run on a failed gate; retain an explicit failure record rather than silently repairing or substituting output.

## What the current checks test

The mandatory `validate_dataset` gate verifies the dataset hash, text hashes, unique IDs, nonempty text and sections, valid JD associations, and nonempty candidate pools. `validate_rankings` checks pool equality, duplicate candidates, rank sequence, finite scores, descending score plus ID order, and top-five flags. The optional GX suite checks candidate row count, ID uniqueness/non-nullness, text non-nullness, and JD IDs in the known job set.

GX itself runs ephemerally: no persistent context or suite is saved. Several planned checks, such as blinded judgments, nonoverlapping JD partitions, audit-field exclusion, and review-queue completeness, are not currently implemented as GX expectations.

## Code walkthrough

1. `jobmatch.cli.main()` reads the dataset JSON and calls `validate_dataset()`.
2. `validate_dataset()` recomputes the dataset hash, checks nonempty jobs/candidates, unique IDs, text and sections, text hashes, valid JD links, and nonempty pools. Any mismatch raises `ValueError` and stops the run.
3. If `--gx` was requested, `great_expectations_validate()` builds an in-memory pandas source, DataFrame asset, batch definition, and expectation suite in an ephemeral GX context.
4. GX evaluates candidate row count, unique/non-null IDs, non-null text, and valid JD IDs. A failed result raises `ValueError`; a passing result returns GX statistics.
5. After each method scores, the runner calls `validate_rankings(rows, pool)`. It checks exact pool coverage, unique candidate IDs, sequential ranks, finite scores, sorting, and shortlist flags.
6. A ranking validation failure is caught by the method loop, stored with its JD, algorithm, error type, and reason in `run.json` under `failures`; the run status becomes `incomplete`.

The standalone `validate.py` entry point adds `--gx` before dispatching, so its command runs both the lightweight checks and GX. The normal matching command always runs the lightweight checks and runs GX only with `--gx`.

## Setup and use

Install the optional MLOps requirements, then validate a prepared dataset:

```powershell
python 02-great-expectations/validate.py --dataset data/prepared/dataset.json
```

To run a matching experiment with the GX input gate enabled:

```powershell
python -m jobmatch run --dataset data/prepared/dataset.json --methods bm25 tfidf --gx
```

The standalone script invokes the GX check. Ranking checks run in the standard matcher after scoring, regardless of `--gx`.

## What discrepancy does validation catch?

A stale or altered text hash reveals that a prepared document no longer matches its recorded content. A method returning only part of a pool, duplicate candidate IDs, NaN scores, or a rank/shortlist mismatch fails ranking validation before it is reported as a valid comparison. Review the run’s `failures` list for method-specific failures.

## Discussion points

- Which failures should block a whole vacancy versus only one method?
- Should a missing document be excluded with a visible reason or block the comparison?
- What would be needed to validate recruiter judgment quality and partition leakage?
- Which checks are structural and which require a human decision about meaning?

## Limits

Passing validation means only that implemented structural checks passed. It does not prove the candidate pool is representative, the extracted text is accurate, a score is useful, or hiring decisions are lawful or fair. GX is optional; core Python checks are mandatory.

## Next stage

[MLflow](../03-mlflow/README.md) records the validated run and any available judgment-based metrics.
