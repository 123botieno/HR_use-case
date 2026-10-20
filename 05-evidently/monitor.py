# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import load, save


def monitor(reference_path, current_path, output):
    import pandas as pd
    from evidently import Report, Dataset, DataDefinition
    from evidently.presets import DataDriftPreset

    reference, current = load(reference_path), load(current_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    outputs = []
    # Compare the same vacancy and algorithm: score scales are method-specific.
    for entry in current["results"]:
        matches = [
            e
            for e in reference["results"]
            if (e["jd_id"], e["algorithm"]) == (entry["jd_id"], entry["algorithm"])
        ]
        if not matches:
            outputs.append(
                {
                    "jd_id": entry["jd_id"],
                    "algorithm": entry["algorithm"],
                    "status": "no_reference",
                }
            )
            continue

        def frame(e):
            return pd.DataFrame(
                {
                    "score": [r["score"] for r in e["ranking"]],
                    "cv_characters": [r.get("cv_characters", 0) for r in e["ranking"]],
                }
            )

        definition = DataDefinition(numerical_columns=["score", "cv_characters"])
        report = Report([DataDriftPreset()]).run(
            reference_data=Dataset.from_pandas(
                frame(matches[0]), data_definition=definition
            ),
            current_data=Dataset.from_pandas(frame(entry), data_definition=definition),
        )
        name = entry["jd_id"] + "-" + entry["algorithm"]
        report.save_html(str(output / (name + ".html")))
        save(output / (name + ".json"), report.dict())
        before = [r["candidate_id"] for r in matches[0]["ranking"][:5]]
        after = [r["candidate_id"] for r in entry["ranking"][:5]]
        shared = set(before) & set(after)
        union = set(before) | set(after)
        outputs.append(
            {
                "jd_id": entry["jd_id"],
                "algorithm": entry["algorithm"],
                "status": "reported",
                "shortlist_jaccard": len(shared) / len(union) if union else None,
                "shared_top5": len(shared),
                "same_pool": matches[0]["pool_hash"] == entry["pool_hash"],
                "same_config": matches[0]["config"] == entry["config"],
            }
        )
    save(output / "index.json", outputs)
    return outputs


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["monitor"] + sys.argv[1:]))
