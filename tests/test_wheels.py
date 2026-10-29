"""Exercise the release inventory boundary, including plausible bad artifacts."""

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WheelInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.version = json.loads((ROOT / "source.json").read_text())["version"]
        for platform in (
            "win_amd64",
            "win_arm64",
            "manylinux2014_x86_64.manylinux_2_17_x86_64",
            "manylinux2014_aarch64.manylinux_2_17_aarch64",
            "macosx_11_0_arm64",
        ):
            for python in ("cp312", "cp313", "cp314"):
                self.write_wheel(platform, python)

    def write_wheel(self, platform, python, metadata_version=None):
        path = self.directory / (
            f"dinkster_opentimelineio-{self.version}-{python}-{python}-{platform}.whl"
        )
        with zipfile.ZipFile(path, "w") as wheel:
            wheel.writestr(
                f"dinkster_opentimelineio-{self.version}.dist-info/METADATA",
                "Metadata-Version: 2.1\nName: dinkster-opentimelineio\n"
                f"Version: {metadata_version or self.version}\n",
            )
        return path

    def validate(self):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/validate_wheels.py"),
                str(self.directory),
                "--target",
                "all",
                "--full",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_complete_release_has_one_hash_per_wheel(self):
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len((self.directory / "SHA256SUMS").read_text().splitlines()), 15)

    def test_one_missing_arm_interpreter_rejects_release(self):
        self.write_wheel("win_arm64", "cp313").unlink()
        result = self.validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing wheel targets", result.stderr)
        self.assertFalse((self.directory / "SHA256SUMS").exists())

    def test_metadata_version_mismatch_rejects_release(self):
        self.write_wheel("win_amd64", "cp314", "0.18.1")
        result = self.validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("metadata disagrees", result.stderr)


if __name__ == "__main__":
    unittest.main()
