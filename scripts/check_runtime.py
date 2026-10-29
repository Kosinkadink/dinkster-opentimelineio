"""Check the installed distribution without changing upstream schema labels."""

import importlib.metadata
import json
from pathlib import Path

import opentimelineio

pin = json.loads((Path(__file__).resolve().parents[1] / "source.json").read_text())
assert importlib.metadata.version("dinkster-opentimelineio") == pin["version"]
assert opentimelineio.__version__ == pin["upstream_version"]
print("Installed distribution:", importlib.metadata.version("dinkster-opentimelineio"))
print("Upstream runtime:", opentimelineio.__version__)
