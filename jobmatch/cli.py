"""Command-line entry points for HR document preparation and matching."""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from common.io import load, save
from common.stages import stage
from common.validation import validate_dataset

prepare = stage("data").prepare
execute = stage("matching").execute
compare = stage("comparison").compare
judgments_from_csv = stage("comparison").judgments_from_csv


def main(argv=None):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    parser = argparse.ArgumentParser(description="HR shortlist matching and evaluation")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_p = commands.add_parser("prepare")
    prepare_p.add_argument("--source", required=True)
    prepare_p.add_argument("--output", default="data/prepared")

    run_p = commands.add_parser("run")
    run_p.add_argument("--dataset", default="data/prepared/dataset.json")
    run_p.add_argument("--output", default="runs")
    run_p.add_argument(
        "--methods", nargs="+", choices=["bm25", "tfidf", "llm"],
        default=["bm25", "tfidf", "llm"],
    )
    run_p.add_argument("--rubric")
    run_p.add_argument("--jd", nargs="+")
    run_p.add_argument("--pool-scope", choices=["vacancy", "all"], default="vacancy")
    run_p.add_argument("--allow-draft-rubric", action="store_true")
    run_p.add_argument("--llm-workers", type=int, default=1)

    validate_p = commands.add_parser("validate")
    validate_p.add_argument("--dataset", default="data/prepared/dataset.json")

    compare_p = commands.add_parser("compare")
    compare_p.add_argument("--run", required=True)
    compare_p.add_argument("--judgments")
    compare_p.add_argument("--output")

    audit_p = commands.add_parser("audit")
    audit_p.add_argument("--run", required=True)
    audit_p.add_argument("--groups", required=True)
    audit_p.add_argument("--judgments")
    audit_p.add_argument("--output", default="runs/audit.json")

    rubric_p = commands.add_parser("rubric-template")
    rubric_p.add_argument("--dataset", default="data/prepared/dataset.json")
    rubric_p.add_argument("--output", default="data/rubric.json")

    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.source, args.output)
        elif args.command == "validate":
            result = validate_dataset(load(args.dataset))
        elif args.command == "run":
            directory, run = execute(
                args.dataset, args.output, args.methods, args.rubric, args.jd,
                args.pool_scope, args.allow_draft_rubric, args.llm_workers,
            )
            result = {
                "directory": str(directory),
                "status": run["status"],
                "successful_methods": len(run["results"]),
                "failures": run["failures"],
            }
            print(json.dumps(result, indent=2))
            return 0 if run["status"] == "complete" else 2
        elif args.command == "compare":
            result = compare(
                load(args.run),
                judgments_from_csv(args.judgments) if args.judgments else None,
            )
            save(args.output or Path(args.run).parent / "comparison.json", result)
        elif args.command == "audit":
            result = stage("fairlearn").audit(
                args.run, args.groups, args.output,
                judgments_from_csv(args.judgments) if args.judgments else None,
            )
        else:
            data = load(args.dataset)
            result = stage("data").build_rubric(data)
            save(args.output, result)
            result = {"path": args.output, "note": "Review and confirm each rubric item before LLM scoring"}

        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
