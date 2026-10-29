"""Reject incomplete or incorrectly named wheel sets before publication."""

import argparse
import hashlib
import json
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.utils import canonicalize_name, parse_wheel_filename

TARGETS = {
    "linux-x86_64": ("manylinux", "_x86_64"),
    "linux-aarch64": ("manylinux", "_aarch64"),
    "windows-x64": ("win_amd64", "win_amd64"),
    "windows-arm64": ("win_arm64", "win_arm64"),
    "macos-arm64": ("macosx_", "_arm64"),
}


def validate(directory: Path, target: str, full: bool) -> None:
    pin = json.loads((Path(__file__).resolve().parents[1] / "source.json").read_text())
    targets = set(TARGETS) if target == "all" else {target}
    interpreters = {"cp312", "cp313", "cp314"} if full else {"cp314"}
    expected = {(platform, python) for platform in targets for python in interpreters}
    found = set()
    hashes = []
    for path in sorted(directory.glob("*.whl")):
        name, version, build, tags = parse_wheel_filename(path.name)
        if name != "dinkster-opentimelineio" or str(version) != pin["version"] or build:
            raise ValueError(f"Unexpected distribution identity: {path.name}")
        cells = set()
        for tag in tags:
            matches = [
                key
                for key, (prefix, suffix) in TARGETS.items()
                if tag.platform.startswith(prefix) and tag.platform.endswith(suffix)
            ]
            if len(matches) != 1 or tag.abi != tag.interpreter:
                raise ValueError(f"Unexpected platform or ABI: {path.name}")
            cells.add((matches[0], tag.interpreter))
        if len(cells) != 1 or not cells <= expected or cells & found:
            raise ValueError(f"Duplicate or unexpected wheel target: {path.name}")
        with zipfile.ZipFile(path) as wheel:
            metadata_files = [n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")]
            if len(metadata_files) != 1:
                raise ValueError(f"Expected one METADATA file: {path.name}")
            metadata = BytesParser().parsebytes(wheel.read(metadata_files[0]))
            if canonicalize_name(metadata["Name"]) != name or metadata["Version"] != str(version):
                raise ValueError(f"Wheel metadata disagrees with filename: {path.name}")
        found.update(cells)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append(f"{digest}  {path.name}")
    if found != expected:
        raise ValueError(f"Missing wheel targets: {sorted(expected - found)}")
    (directory / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="ascii")
    print(f"Validated {len(found)} wheels for {sorted(targets)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--target", choices=[*TARGETS, "all"], required=True)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    validate(args.directory, args.target, args.full)
