# dinkster-opentimelineio

Downstream binary builds of [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO).
The PyPI distribution is `dinkster-opentimelineio`; Python code still uses
`import opentimelineio`. Do not install this distribution alongside upstream
`opentimelineio`: they own the same import package and console commands.

## Versions and source

`source.json` records the exact upstream repository, commit, original version
and downstream distribution version. The initial source is upstream's
`0.19.0.dev1` snapshot, not an upstream stable release. Its downstream version
is `0.19.0.post1`. For a new upstream version X.Y.Z use X.Y.Z.post1; increment
the post number for subsequent snapshots or packaging fixes of that version.
Post releases sort after X.Y.Z and have no PyPI-incompatible local version label.
The Git tag is `v` followed by the exact downstream version in `source.json`.

`importlib.metadata.version('dinkster-opentimelineio')` returns the downstream
distribution version. `opentimelineio.__version__` deliberately retains the
upstream version because OTIO uses it for schema compatibility labels.
Submodules are checked out recursively at their upstream pins. Release artifacts
include source/submodule provenance, wheel SHA256SUMS and the upstream license.

## Wheel matrix

Every release contains fifteen regular CPython wheels (not free-threaded or abi3):

| Target | CPython | Hosted runner | Wheel platform |
| --- | --- | --- | --- |
| Linux x86_64 | 3.12, 3.13, 3.14 | ubuntu-24.04 | manylinux2014 x86_64 |
| Linux aarch64 | 3.12, 3.13, 3.14 | ubuntu-24.04-arm | manylinux2014 aarch64 |
| Windows x64 | 3.12, 3.13, 3.14 | windows-2022 | win_amd64 |
| Windows ARM64 | 3.12, 3.13, 3.14 | windows-11-arm | win_arm64 |
| macOS arm64 | 3.12, 3.13, 3.14 | macos-15 | macosx_11_0_arm64 or newer |

All builds and upstream unittest runs execute natively on hosted runners.
Windows builds install zlib with vcpkg and repair wheels with delvewheel.
Linux uses auditwheel through cibuildwheel; macOS uses its delocate repair.
Intel macOS, musllinux, PyPy and abi3 are not built.

`ci.yml` builds cp314 on Linux x86_64 and Windows x64 on pull requests and main.
`release.yml` rehearses all fifteen wheels on pull requests changing its build
files, and builds/releases/publishes on version tags. PR rehearsals upload
`release-wheels` artifacts but skip both GitHub release creation and PyPI
publication. There is no manual dispatch trigger. Both workflows use `build.yml`
so repair and testing behavior stay synchronized.

## Repin and release

1. Select an upstream commit, read its changes and record its full SHA and
   original setup.py version in `source.json`. Increment the downstream version.
2. Review the pinned setup.py and submodules. `scripts/prepare_source.py` checks
   the commit/submodule identities and fails if the expected source fields
   changed; update it deliberately when upstream packaging changes.
3. Open a pull request. Require reduced CI plus the full release rehearsal;
   inspect all fifteen wheel identities, upstream tests and installed imports.
   Run local checks with `python -m unittest discover -s tests` (requires
   `packaging`), plus the repository's Python lint/format checks.
4. After review and merge, confirm the pending publisher below is registered.
   An authorized release operator pushes the version tag at the approved
   landed commit. Do not tag or publish merely to test the workflow.
5. Inspect the tag run, GitHub release assets and PyPI files. Download binary
   wheels for each supported Python/platform, then test native imports.
   Never replace a published version; fix the pin/build and increment the
   downstream post number for the next release.

The pinned upstream setup.py lacks a `win-arm64` CMake generator mapping.
Source preparation adds `win-arm64: ARM64` beside its existing x64 mapping;
without it, Windows ARM64 fails before CMake generation. This build-only fix
does not alter OTIO runtime or schema code. macOS sets
`CMAKE_OSX_ARCHITECTURES=arm64` to avoid upstream's universal2 default. Distribution
name/version overrides are packaging-only; upstream attribution is retained.

## Trusted publisher

Register these names as the PyPI pending trusted publisher before the first tag:

| Field | Value |
| --- | --- |
| PyPI project | dinkster-opentimelineio |
| GitHub owner | Kosinkadink |
| GitHub repository | dinkster-opentimelineio |
| Workflow filename | release.yml |
| GitHub environment | pypi |

The publish job alone receives `id-token: write` and uses
`pypa/gh-action-pypi-publish` in environment `pypi`. No API token or password is
needed. Release assets are attached before the publication job runs; a failed
publication does not erase built wheels or their provenance.

## License

OpenTimelineIO is Apache-2.0 licensed. Every release includes the upstream
`LICENSE.txt` as `OpenTimelineIO-LICENSE.txt`; wheels retain upstream licensing
and attribution.
