"""Apply downstream distribution metadata to the pinned upstream checkout."""

import argparse
import json
import subprocess
from pathlib import Path


def prepare(source: Path) -> None:
    pin = json.loads((Path(__file__).resolve().parents[1] / "source.json").read_text())
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != pin["commit"]:
        raise ValueError("Source checkout differs from source.json")
    status = subprocess.check_output(
        ["git", "-C", str(source), "submodule", "status", "--recursive"], text=True
    ).splitlines()
    if not status or any(not line.startswith(" ") for line in status):
        raise ValueError("Submodules differ from the pinned upstream tree")
    path = source / "setup.py"
    original = path.read_text(encoding="utf-8")
    replacements = {
        "name='OpenTimelineIO'": "name='dinkster-opentimelineio'",
        f'"version": "{pin["upstream_version"]}"': f'"version": "{pin["version"]}"',
    }
    updated = original
    for old, new in replacements.items():
        if updated.count(old) != 1:
            raise ValueError(f"Expected exactly one upstream metadata field: {old}")
        updated = updated.replace(old, new)
    path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    prepare(parser.parse_args().source)
