# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import load, save, read_csv, write_csv


def make_synthetic_scenario(run_path, output_dir, penalty=1.0):
    """Create paired baseline/biased teaching runs and synthetic audit labels."""
    if penalty <= 0:
        raise ValueError("Penalty must be greater than zero")

    run = load(run_path)
    baseline = load(run_path)
    biased = load(run_path)
    group_mapping, judgment_mapping = {}, {}
    first_ranking_by_jd = {}

    for entry in run["results"]:
        ranking = entry["ranking"]
        candidates = sorted(row["candidate_id"] for row in ranking)
        if len(candidates) < 2:
            raise ValueError(
                f"Synthetic audit needs at least two candidates for {entry['jd_id']}"
            )
        score_order = sorted(ranking, key=lambda row: (-float(row["score"]), row["candidate_id"]))
        if entry["jd_id"] not in first_ranking_by_jd:
            first_ranking_by_jd[entry["jd_id"]] = score_order
        first_order = first_ranking_by_jd[entry["jd_id"]]
        groups = {
            row["candidate_id"]: ("Group B" if i % 2 == 0 else "Group A")
            for i, row in enumerate(first_order)
        }
        suitable_ids = {
            row["candidate_id"] for row in score_order[: min(10, len(score_order))]
        }

        for cid in candidates:
            group_mapping[(entry["jd_id"], cid)] = groups[cid]
            suitable = int(cid in suitable_ids)
            judgment_mapping[(entry["jd_id"], cid)] = {
                    "jd_id": entry["jd_id"],
                    "candidate_id": cid,
                    "suitable": suitable,
                    "relevance": 1 if suitable else 0,
                }

    for entry in biased["results"]:
        ranking = entry["ranking"]
        score_order = sorted(ranking, key=lambda row: (-float(row["score"]), row["candidate_id"]))
        groups = {
            cid: group
            for (jd, cid), group in group_mapping.items()
            if jd == entry["jd_id"]
        }
        group_b_scores = [
            float(row["score"])
            for row in ranking
            if groups[row["candidate_id"]] == "Group B"
        ]
        group_a_scores = [
            float(row["score"])
            for row in ranking
            if groups[row["candidate_id"]] == "Group A"
        ]
        if group_a_scores and group_b_scores:
            required_penalty = max(group_b_scores) - min(group_a_scores) + 1.0
        else:
            required_penalty = penalty
        applied_penalty = max(penalty, required_penalty)
        entry["synthetic_penalty_applied"] = applied_penalty
        for row in ranking:
            if groups[row["candidate_id"]] == "Group B":
                row["score"] = float(row["score"]) - applied_penalty
        ranking.sort(key=lambda row: (-float(row["score"]), row["candidate_id"]))
        for position, row in enumerate(ranking, 1):
            row["rank"] = position
            row["shortlisted"] = position <= 5
            row["cutoff_tie"] = False

    baseline["fairness_synthetic"] = {
        "kind": "baseline",
        "description": "Synthetic teaching scenario; groups and suitability labels are invented.",
    }
    biased["fairness_synthetic"] = {
        "kind": "biased",
        "penalized_group": "Group B",
        "score_penalty_at_least": penalty,
        "description": "Synthetic teaching scenario; Group B receives a penalty large enough to move below Group A in ranking.",
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save(output_dir / "baseline_run.json", baseline)
    save(output_dir / "biased_run.json", biased)
    write_csv(
        output_dir / "audit_groups.csv",
        [
            {"jd_id": jd, "candidate_id": cid, "group": group}
            for (jd, cid), group in sorted(group_mapping.items())
        ],
    )
    write_csv(
        output_dir / "synthetic_judgments.csv",
        [judgment_mapping[key] for key in sorted(judgment_mapping)],
    )
    return {
        "baseline_run": str(output_dir / "baseline_run.json"),
        "biased_run": str(output_dir / "biased_run.json"),
        "groups": str(output_dir / "audit_groups.csv"),
        "judgments": str(output_dir / "synthetic_judgments.csv"),
        "penalty": penalty,
        "note": "Synthetic teaching artifacts only; groups and suitability labels are invented.",
    }


def audit(run_path, audit_csv, output, judgments=None, minimum_group_size=5):
    import pandas as pd
    from fairlearn.metrics import MetricFrame, selection_rate
    from sklearn.metrics import recall_score

    run = load(run_path)
    audit_rows = read_csv(audit_csv)
    mapping = {}
    for row in audit_rows:
        key = (row["jd_id"], row["candidate_id"])
        if key in mapping or not row.get("group"):
            raise ValueError("Duplicate audit ID or empty group")
        mapping[key] = row["group"]
    known = {
        (e["jd_id"], r["candidate_id"]) for e in run["results"] for r in e["ranking"]
    }
    if set(mapping) - known:
        raise ValueError("Audit IDs outside this run")
    results = []
    for entry in run["results"]:
        records = []
        for row in entry["ranking"]:
            key = (entry["jd_id"], row["candidate_id"])
            if key in mapping:
                records.append(
                    {
                        "group": mapping[key],
                        "selected": int(row["shortlisted"]),
                        "suitable": (judgments or {}).get(key, {}).get("suitable"),
                    }
                )
        if not records:
            continue
        frame = pd.DataFrame(records)
        metrics = {"selection_rate": selection_rate}
        complete_labels = frame["suitable"].notna().all()
        if complete_labels:
            metrics["recall"] = lambda y, p: recall_score(y, p, zero_division=0)
        measured = MetricFrame(
            metrics=metrics,
            y_true=frame["suitable"].astype(float).fillna(0).astype(int),
            y_pred=frame["selected"],
            sensitive_features=frame["group"],
        )
        groups = []
        for group, values in measured.by_group.iterrows():
            count = int((frame["group"] == group).sum())
            suitable_in_group = int(
                frame.loc[frame["group"] == group, "suitable"]
                .astype(float)
                .fillna(0)
                .sum()
            )
            groups.append(
                {
                    "group": str(group),
                    "count": count,
                    "sufficient_sample": count >= minimum_group_size,
                    **{
                        name: (
                            None
                            if name == "recall" and suitable_in_group == 0
                            else float(value)
                        )
                        for name, value in values.items()
                    },
                }
            )
        results.append(
            {
                "jd_id": entry["jd_id"],
                "algorithm": entry["algorithm"],
                "audit_coverage": len(records) / len(entry["ranking"]),
                "group_metrics": groups,
                "recall_labels_complete_for_audited_subset": bool(complete_labels),
            }
        )
    report = {
        "results": results,
        "minimum_group_size": minimum_group_size,
        "note": "Descriptive audit only; small samples and missing groups limit conclusions. No attributes inferred.",
    }
    save(output, report)
    return report


def compare_synthetic(baseline_path, biased_path, audit_csv, output, judgments):
    """Audit paired synthetic runs and summarize per-vacancy metric changes."""
    baseline = audit(baseline_path, audit_csv, Path(output).with_name("baseline_audit.json"), judgments)
    biased = audit(biased_path, audit_csv, Path(output).with_name("biased_audit.json"), judgments)
    def key(result):
        return (result["jd_id"], result["algorithm"])

    baseline_rows = {key(row): row for row in baseline["results"]}
    biased_rows = {key(row): row for row in biased["results"]}
    comparisons = []
    for identity in sorted(set(baseline_rows) & set(biased_rows)):
        left = baseline_rows[identity]
        right = biased_rows[identity]
        left_groups = {row["group"]: row for row in left["group_metrics"]}
        right_groups = {row["group"]: row for row in right["group_metrics"]}
        groups = []
        for group in sorted(set(left_groups) & set(right_groups)):
            before, after = left_groups[group], right_groups[group]
            groups.append(
                {
                    "group": group,
                    "count": before["count"],
                    "baseline_selection_rate": before["selection_rate"],
                    "biased_selection_rate": after["selection_rate"],
                    "selection_rate_change": after["selection_rate"] - before["selection_rate"],
                    "baseline_recall": before.get("recall"),
                    "biased_recall": after.get("recall"),
                    "recall_change": (
                        after["recall"] - before["recall"]
                        if before.get("recall") is not None and after.get("recall") is not None
                        else None
                    ),
                }
            )
        comparisons.append({"jd_id": identity[0], "algorithm": identity[1], "groups": groups})
    report = {
        "synthetic": True,
        "per_jd": comparisons,
        "note": "Invented groups and suitability labels; demonstrates capture of an injected score penalty, not real-world fairness.",
    }
    save(output, report)
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fairlearn group audit and synthetic teaching scenario")
    commands = parser.add_subparsers(dest="command", required=True)
    scenario = commands.add_parser("scenario", help="Create paired synthetic teaching artifacts")
    scenario.add_argument("--run", required=True)
    scenario.add_argument("--output-dir", required=True)
    scenario.add_argument("--penalty", type=float, default=1.0)
    audit_parser = commands.add_parser("audit", help="Audit group selection and recall")
    audit_parser.add_argument("--run", required=True)
    audit_parser.add_argument("--groups", required=True)
    audit_parser.add_argument("--judgments")
    audit_parser.add_argument("--output", required=True)
    compare_parser = commands.add_parser("compare-synthetic", help="Compare baseline and biased teaching runs")
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--biased", required=True)
    compare_parser.add_argument("--groups", required=True)
    compare_parser.add_argument("--judgments", required=True)
    compare_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "scenario":
        result = make_synthetic_scenario(args.run, args.output_dir, args.penalty)
    elif args.command == "audit":
        from jobmatch.cli import judgments_from_csv

        result = audit(
            args.run,
            args.groups,
            args.output,
            judgments_from_csv(args.judgments) if args.judgments else None,
        )
    else:
        from jobmatch.cli import judgments_from_csv

        result = compare_synthetic(
            args.baseline,
            args.biased,
            args.groups,
            args.output,
            judgments_from_csv(args.judgments),
        )
    print(__import__("json").dumps(result, indent=2))
