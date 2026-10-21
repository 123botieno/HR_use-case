"""Generate deterministic, fictional HR data for fairness teaching only."""

# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import random
from common.io import digest, save, write_csv


GROUP_COLUMNS = ("gender", "ethnicity", "economic_class", "geography")


def _ranking(jd_id, records, score_field):
    ordered = sorted(
        records, key=lambda row: (-row[score_field], row["candidate_id"])
    )
    ranking = []
    cutoff_tie = len(ordered) > 5 and ordered[4][score_field] == ordered[5][score_field]
    for position, row in enumerate(ordered, 1):
        ranking.append(
            {
                "jd_id": jd_id,
                "candidate_id": row["candidate_id"],
                "algorithm": "synthetic_historical_shortlisting",
                "score": float(row[score_field]),
                "rank": position,
                "shortlisted": position <= 5,
                "cutoff_tie": bool(
                    cutoff_tie and row[score_field] == ordered[4][score_field]
                ),
                "uninformative": False,
            }
        )
    return ranking


def generate(output_dir, seed=20261020, vacancy_count=8, applicants_per_vacancy=120):
    """Write synthetic application rows, paired ranking runs, and audit tables."""
    if vacancy_count < 1 or applicants_per_vacancy < 10:
        raise ValueError("Use at least one vacancy and ten applicants per vacancy")

    rng = random.Random(seed)
    applications = []
    baseline_results, historical_results = [], []
    judgments = []

    for vacancy_number in range(1, vacancy_count + 1):
        jd_id = f"SYN-JD-{vacancy_number:02d}"
        rows = []
        for applicant_number in range(1, applicants_per_vacancy + 1):
            candidate_id = f"SYN-{vacancy_number:02d}-{applicant_number:04d}"
            gender = rng.choices(
                ["Woman", "Man", "Nonbinary"], weights=[0.49, 0.49, 0.02]
            )[0]
            ethnicity = rng.choices(
                ["Ethnicity A", "Ethnicity B", "Ethnicity C", "Ethnicity D"],
                weights=[0.38, 0.30, 0.20, 0.12],
            )[0]
            economic_class = rng.choices(
                ["Low", "Middle", "High"], weights=[0.48, 0.38, 0.14]
            )[0]
            geography = rng.choices(
                ["Capital city", "Other urban", "Rural", "Pastoral/remote"],
                weights=[0.18, 0.32, 0.34, 0.16],
            )[0]

            skill_match = rng.randint(25, 100)
            relevant_years = rng.randint(0, 15)
            required_certificate = int(rng.random() < 0.58)
            baseline_score = round(
                0.72 * skill_match
                + min(relevant_years, 10) * 1.7
                + required_certificate * 8,
                3,
            )
            suitable = int(
                skill_match >= 62
                and relevant_years >= 3
                and required_certificate == 1
            )

            # Synthetic historical bias: explicit group penalties plus access proxies.
            gender_penalty = {"Woman": -5.0, "Man": 0.0, "Nonbinary": -5.0}[gender]
            ethnicity_penalty = {
                "Ethnicity A": 0.0,
                "Ethnicity B": -2.0,
                "Ethnicity C": -5.0,
                "Ethnicity D": -8.0,
            }[ethnicity]
            class_penalty = {"Low": -7.0, "Middle": -2.0, "High": 0.0}[
                economic_class
            ]
            geography_penalty = {
                "Capital city": 0.0,
                "Other urban": -1.0,
                "Rural": -4.0,
                "Pastoral/remote": -7.0,
            }[geography]
            elite_access = int(
                rng.random()
                < {"Low": 0.12, "Middle": 0.38, "High": 0.72}[economic_class]
            )
            advanced_english = int(
                rng.random()
                < {
                    "Capital city": 0.78,
                    "Other urban": 0.58,
                    "Rural": 0.34,
                    "Pastoral/remote": 0.24,
                }[geography]
            )
            proxy_bonus = elite_access * 3.0 + advanced_english * 2.0
            historical_score = round(
                baseline_score
                + gender_penalty
                + ethnicity_penalty
                + class_penalty
                + geography_penalty
                + proxy_bonus,
                3,
            )
            rows.append(
                {
                    "jd_id": jd_id,
                    "candidate_id": candidate_id,
                    "gender": gender,
                    "ethnicity": ethnicity,
                    "economic_class": economic_class,
                    "geography": geography,
                    "skill_match": skill_match,
                    "relevant_years": relevant_years,
                    "required_certificate": required_certificate,
                    "elite_access_proxy": elite_access,
                    "advanced_english_proxy": advanced_english,
                    "qualification_score": baseline_score,
                    "historical_score": historical_score,
                    "suitable": suitable,
                    "gender_score_effect": gender_penalty,
                    "ethnicity_score_effect": ethnicity_penalty,
                    "economic_class_score_effect": class_penalty,
                    "geography_score_effect": geography_penalty,
                    "proxy_score_effect": proxy_bonus,
                }
            )

        baseline_ranking = _ranking(jd_id, rows, "qualification_score")
        historical_ranking = _ranking(jd_id, rows, "historical_score")
        baseline_top = {row["candidate_id"] for row in baseline_ranking[:5]}
        historical_top = {row["candidate_id"] for row in historical_ranking[:5]}
        for row in rows:
            row["baseline_shortlisted"] = int(row["candidate_id"] in baseline_top)
            row["historical_shortlisted"] = int(
                row["candidate_id"] in historical_top
            )
            # Hiring outcomes are observed only for people who were shortlisted.
            # Blank means unknown, not a negative hiring outcome.
            row["historical_hired"] = (
                int(rng.random() < 0.35)
                if row["historical_shortlisted"]
                else None
            )
            applications.append(row)
            judgments.append(
                {
                    "jd_id": jd_id,
                    "candidate_id": row["candidate_id"],
                    "suitable": row["suitable"],
                    "relevance": 1 if row["suitable"] else 0,
                }
            )

        pool_hash = digest(
            [(row["candidate_id"], row["qualification_score"]) for row in rows]
        )
        for ranking, target in (
            (baseline_ranking, baseline_results),
            (historical_ranking, historical_results),
        ):
            target.append(
                {
                    "jd_id": jd_id,
                    "job_family": "Synthetic demonstration",
                    "algorithm": "synthetic_historical_shortlisting",
                    "pool_hash": pool_hash,
                    "config": {
                        "score_source": (
                            "qualification_score"
                            if target is baseline_results
                            else "historical_score"
                        )
                    },
                    "runtime_seconds": 0.0,
                    "ranking": ranking,
                }
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "synthetic_historical_hr.csv", applications)
    write_csv(output_dir / "synthetic_suitability_judgments.csv", judgments)

    for dimension in GROUP_COLUMNS:
        write_csv(
            output_dir / f"audit_groups_{dimension}.csv",
            [
                {
                    "jd_id": row["jd_id"],
                    "candidate_id": row["candidate_id"],
                    "group": row[dimension],
                }
                for row in applications
            ],
        )

    common = {
        "run_id": f"synthetic-{seed}",
        "version": "synthetic-hr-demo-v1",
        "dataset_hash": digest(applications),
        "requested_methods": ["synthetic_historical_shortlisting"],
        "pool_scope": "synthetic applications by vacancy",
        "status": "complete",
        "failures": [],
    }
    save(
        output_dir / "qualification_baseline_run.json",
        {**common, "scenario": "unbiased synthetic qualification baseline", "results": baseline_results},
    )
    save(
        output_dir / "biased_historical_run.json",
        {
            **common,
            "scenario": "synthetic historical process with explicit group penalties and access proxies",
            "results": historical_results,
        },
    )
    metadata = {
        "synthetic": True,
        "seed": seed,
        "vacancy_count": vacancy_count,
        "applicants_per_vacancy": applicants_per_vacancy,
        "application_count": len(applications),
        "shortlist_size_per_vacancy": 5,
        "historical_outcome_observation": {
            "observed_only_for": "historical_shortlisted == 1",
            "observed_count": sum(row["historical_shortlisted"] for row in applications),
            "missing_count": sum(not row["historical_shortlisted"] for row in applications),
            "meaning": "historical_hired is blank for applicants outside the historical shortlist; blank means outcome not observed, not not hired",
        },
        "dimensions": list(GROUP_COLUMNS),
        "bias_recipe": {
            "gender": "Woman and Nonbinary groups receive -5 score points",
            "ethnicity": "Ethnicity B/C/D receive -2/-5/-8 score points",
            "economic_class": "Low/Middle receive -7/-2 score points",
            "geography": "Other urban/Rural/Pastoral-remote receive -1/-4/-7 score points",
            "proxies": "Elite-access and advanced-English indicators add score points and are more common in advantaged strata",
        },
        "suitability_definition": "Synthetic job-related rule: skill_match >= 62, relevant_years >= 3, and required_certificate == 1; independent of group fields",
        "interpretation": "All records, identities, labels, scores, and historical decisions are fabricated. Do not treat them as real HR evidence or as a legal fairness determination.",
    }
    save(output_dir / "metadata.json", metadata)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="04-fairlearn/synthetic_hr_demo")
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--vacancies", type=int, default=8)
    parser.add_argument("--applicants-per-vacancy", type=int, default=120)
    args = parser.parse_args()
    print(
        __import__("json").dumps(
            generate(
                args.output,
                args.seed,
                args.vacancies,
                args.applicants_per_vacancy,
            ),
            indent=2,
        )
    )
