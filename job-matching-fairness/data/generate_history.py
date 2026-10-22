"""Rebuild the entirely fictional historical hiring exercise with a fixed seed."""

import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "candidate_cvs" / "candidates.csv"
OUTPUT = ROOT / "historical_hiring_synthetic.csv"
SEED = 20261022


def generate():
    rng = random.Random(SEED)
    with INPUT.open(encoding="utf-8", newline="") as stream:
        candidates = list(csv.DictReader(stream))
    by_job = {}
    for candidate in candidates:
        by_job.setdefault(candidate["job_id"], []).append(candidate)
    rows = []
    for job_id, pool in sorted(by_job.items()):
        # Group assignment is randomized independently of the qualification tier.
        for candidate in pool:
            candidate["sex"] = rng.choice(["Woman", "Man"])
            candidate["geographic_location"] = rng.choice(
                ["Addis Ababa", "Outside Addis Ababa"]
            )
            # This proxy is derived only from profile experience and skill-list length;
            # it is simulated and not a validated suitability label.
            years = float(candidate["experience_years"])
            skill_count = len([s for s in candidate["skills"].split("|") if s.strip()])
            base = min(92, 42 + 2.2 * years + 1.4 * skill_count)
            candidate["simulated_qualification_score"] = round(
                base + rng.uniform(-4, 4), 1
            )
            # The simulated historical process favors men and Addis-based applicants.
            # This mechanism is documented for facilitators, not revealed in the opening.
            candidate["historical_decision_score"] = (
                candidate["simulated_qualification_score"]
                + (9 if candidate["sex"] == "Man" else 0)
                + (7 if candidate["geographic_location"] == "Addis Ababa" else 0)
                + rng.uniform(-5, 5)
            )
        ranked = sorted(pool, key=lambda r: (-r["historical_decision_score"], r["candidate_id"]))
        shortlisted = {r["candidate_id"] for r in ranked[:10]}
        hired = {
            r["candidate_id"] for r in sorted(
                (r for r in ranked if r["candidate_id"] in shortlisted),
                key=lambda r: (-r["simulated_qualification_score"], r["candidate_id"]),
            )[:5]
        }
        for candidate in pool:
            is_shortlisted = candidate["candidate_id"] in shortlisted
            is_hired = candidate["candidate_id"] in hired if is_shortlisted else ""
            performance = (
                round(max(1, min(5, candidate["simulated_qualification_score"] / 20 + rng.uniform(-0.7, 0.7))), 1)
                if is_hired is True else ""
            )
            rows.append({
                "candidate_id": candidate["candidate_id"],
                "job_id": job_id,
                "qualifications": candidate["qualifications"],
                "skills": candidate["skills"],
                "experience_years": candidate["experience_years"],
                "simulated_qualification_score": candidate["simulated_qualification_score"],
                "sex": candidate["sex"],
                "geographic_location": candidate["geographic_location"],
                "historical_shortlisted": int(is_shortlisted),
                "historical_hired": is_hired,
                "post_hire_performance": performance,
                "performance_observed": int(is_hired is True),
            })
    fields = list(rows[0])
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(f"Wrote {generate()} synthetic candidate-job applications to {OUTPUT}")
