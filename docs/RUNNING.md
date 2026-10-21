# Running the HR case

The fairness session uses generated, fictional HR data and saved reports. Follow the three commands in the [repository README](../README.md), then work through the [four-episode Jupyter notebook](../04-fairlearn/HR_Fairness_Learning_Session.ipynb).

The generated cohort, bias recipe, rankings, and Fairlearn outputs are under `04-fairlearn/`. Regenerate the cohort with a fixed seed:

```text
uv run --no-sync --python 3.12 python 04-fairlearn/synthetic_hr.py --output 04-fairlearn/synthetic_hr_demo --seed 20261020 --vacancies 8 --applicants-per-vacancy 120
```

The full HR matching comparison is documented in [07-job-matching](../07-job-matching/README.md). The shared MLOps tools and setup steps belong in the workshop hub; this repository contains only the HR-specific teaching story. See the README for the hub link when it is supplied.
