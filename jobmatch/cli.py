"""Command-line entry points shared by stage scripts."""

from common.stages import stage

import argparse

import json

from pathlib import Path

from dotenv import load_dotenv

from common.io import load, save

prepare = stage("data").prepare

execute = stage("matching").execute

compare = stage("comparison").compare

judgments_from_csv = stage("comparison").judgments_from_csv

validate_dataset = stage("validation").validate_dataset

great_expectations_validate = stage("validation").great_expectations_validate


def main(argv=None):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    parser = argparse.ArgumentParser(
        description="Compare top-five JD/CV matching methods"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_p = commands.add_parser("prepare")
    prepare_p.add_argument("--source", required=True)
    prepare_p.add_argument("--output", default="data/prepared")
    for name in ("run", "flow"):
        p = commands.add_parser(name)
        p.add_argument("--dataset", default="data/prepared/dataset.json")
        p.add_argument("--output", default="runs")
        p.add_argument(
            "--methods",
            nargs="+",
            choices=["bm25", "tfidf", "llm"],
            default=["bm25", "tfidf", "llm"],
        )
        p.add_argument("--rubric")
        p.add_argument("--jd", nargs="+")
        p.add_argument("--gx", action="store_true")
        p.add_argument("--pool-scope", choices=["vacancy", "all"], default="vacancy")
        if name == "run":
            p.add_argument(
                "--allow-draft-rubric",
                action="store_true",
                help="Experimental scoring only; preserve unconfirmed rubric status",
            )
            p.add_argument("--llm-workers", type=int, default=1)
        if name == "flow":
            p.add_argument("--track-uri")
            p.add_argument("--reference")
            p.add_argument("--groups")
            p.add_argument("--judgments")
            p.add_argument("--version-repository")
    p = commands.add_parser("validate")
    p.add_argument("--dataset", default="data/prepared/dataset.json")
    p.add_argument("--gx", action="store_true")
    p = commands.add_parser("compare")
    p.add_argument("--run", required=True)
    p.add_argument("--judgments")
    p.add_argument("--output")
    p = commands.add_parser("version")
    p.add_argument("--path", default="data/prepared")
    p.add_argument("--repository", default=".")
    p = commands.add_parser("track")
    p.add_argument("--run", required=True)
    p.add_argument("--uri", default="sqlite:///mlflow.db")
    p = commands.add_parser("audit")
    p.add_argument("--run", required=True)
    p.add_argument("--groups", required=True)
    p.add_argument("--judgments")
    p.add_argument("--output", default="runs/audit.json")
    p = commands.add_parser("monitor")
    p.add_argument("--reference", required=True)
    p.add_argument("--current", required=True)
    p.add_argument("--output", default="runs/monitoring")
    p = commands.add_parser("rubric-template")
    p.add_argument("--dataset", default="data/prepared/dataset.json")
    p.add_argument("--output", default="data/rubric.json")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.source, args.output)
        elif args.command == "validate":
            data = load(args.dataset)
            result = validate_dataset(data)
            if args.gx:
                result["great_expectations"] = great_expectations_validate(data)
        elif args.command == "run":
            directory, run = execute(
                args.dataset,
                args.output,
                args.methods,
                args.rubric,
                args.jd,
                args.gx,
                args.pool_scope,
                args.allow_draft_rubric,
                args.llm_workers,
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
        elif args.command == "rubric-template":
            data = load(args.dataset)
            result = stage("data").build_rubric(data)
            save(args.output, result)
            result = {
                "path": args.output,
                "note": "Edit and confirm each rubric before LLM scoring",
            }
        else:
            if args.command == "version":
                result = stage("dvc").version_data(args.path, args.repository)
            elif args.command == "track":
                result = stage("mlflow").track(args.run, args.uri)
            elif args.command == "audit":
                result = stage("fairlearn").audit(
                    args.run,
                    args.groups,
                    args.output,
                    judgments_from_csv(args.judgments) if args.judgments else None,
                )
            elif args.command == "monitor":
                result = stage("evidently").monitor(
                    args.reference, args.current, args.output
                )
            else:
                result = stage("prefect").prefect_run(
                    args.dataset,
                    args.output,
                    args.methods,
                    args.rubric,
                    args.jd,
                    args.gx,
                    args.pool_scope,
                    args.track_uri,
                    args.reference,
                    args.groups,
                    args.judgments,
                    args.version_repository,
                )
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
