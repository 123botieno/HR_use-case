"""Restore the locally supplied workshop collection and verify SHA-256 hashes."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="usb_folder", type=Path)
    parser.add_argument("--manifest", type=Path, default=ROOT / "downloads.json")
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    entries = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    for item in entries:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe destination path: {relative}")
        destination = args.output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if args.usb_folder:
            source = args.usb_folder / relative
            if not source.is_file():
                raise FileNotFoundError(f"USB bundle is missing {relative}")
            shutil.copyfile(source, destination)
        elif item.get("url"):
            with urlopen(item["url"], timeout=60) as response, destination.open("wb") as out:
                shutil.copyfileobj(response, out)
        else:
            raise ValueError(
                f"{relative} has no public URL; provide its bundle with --from <USB folder>"
            )
        actual = sha256(destination)
        if actual.lower() != item["sha256"].lower():
            destination.unlink(missing_ok=True)
            raise ValueError(f"SHA-256 mismatch for {relative}: got {actual}")
    print(f"Verified and restored {len(entries)} files.")


if __name__ == "__main__":
    main()
