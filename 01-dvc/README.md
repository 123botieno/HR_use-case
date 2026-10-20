# 01 — DVC: version the data behind each comparison

## Where this fits

DVC records large or changing data products alongside Git. In this project, it can track prepared CV/JD data and evaluation artifacts so a ranking run can be tied to the exact inputs used. DVC does not validate data or run the matching methods; Great Expectations and the matching pipeline handle those steps.

## Flow

1. Prepare and validate a dataset.
2. Initialize Git and DVC in the project repository.
3. Add the prepared data directory to DVC, which creates a `.dvc` pointer and stages the files in the local DVC cache.
4. Commit code and pointer metadata in Git. Configure an approved private DVC remote separately if authorized storage is available.
5. Record the Git revision and dataset hash with the run; restore the referenced version when reproducing it.

## What the current adapter does

`version.py` checks that the requested target is inside the repository and that both `.git` and `.dvc` exist. It invokes `dvc add` and reports that it did not upload anything. It does not initialize a repository, configure a remote, push data, restore a version, or write DVC hashes into MLflow automatically.

## Code walkthrough

1. The script entry point forwards `--path` and `--repository` to the shared CLI's `version` command.
2. `jobmatch.cli.main()` dispatches that command to `version_data()` in [version.py](version.py).
3. `version_data()` resolves both paths and rejects the repository root or any target outside the repository.
4. It checks for `.git` and `.dvc`; missing setup raises a `ValueError` with initialization guidance.
5. It runs `python -m dvc add <relative-target>` from the repository. A nonzero DVC exit stops the command.
6. On success it returns the target path and `uploaded: false`; DVC writes its pointer/cache artifacts. The adapter itself does not push to a remote.

## Setup and use

Install the optional MLOps requirements. Initialize DVC manually in the repository first, then track the prepared data:

```powershell
python 01-dvc/version.py --path data/prepared --repository .
```

The path must exist and be inside the repository. Review the generated pointer, then commit the pointer and relevant `.dvc` metadata. Avoid placing candidate CVs in a public remote; follow the data access and retention rules for the project.

## What discrepancy does DVC help explain?

If a rerun produces different rankings, a changed dataset or source document version may explain the difference. DVC makes data versions addressable; the run artifact separately records dataset, pool, and code hashes. Matching configurations and independent judgments still need to be compared.

## Discussion points

- Which artifacts need versioning: raw CVs, extracted text, rubric, labels, rankings, or all of these?
- Who may read and restore a remote containing personal data?
- How should access revocation and retention work for cached copies?
- Which identifiers and hashes should be recorded in every experiment?

## Limits

DVC storage does not anonymize, encrypt by itself, or authorize sharing. No remote is configured by this adapter. A data hash supports integrity and identity checks; it does not certify that the source data is correct or appropriate.

## Next stage

[Great Expectations](../02-great-expectations/README.md) checks prepared inputs and ranking outputs.
