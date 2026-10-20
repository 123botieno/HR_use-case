# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import subprocess


def version_data(path, repository):
    repository = Path(repository).resolve()
    target = Path(path).resolve()
    if not target.is_relative_to(repository) or target == repository:
        raise ValueError("DVC target must be inside the repository, not its root")
    if not (repository / ".git").exists() or not (repository / ".dvc").exists():
        raise ValueError(
            "Initialize Git and DVC in the repository first; no remote is configured automatically"
        )
    subprocess.run(
        [sys.executable, "-m", "dvc", "add", str(target.relative_to(repository))],
        cwd=repository,
        check=True,
    )
    return {"target": str(target), "uploaded": False}


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["version"] + sys.argv[1:]))
