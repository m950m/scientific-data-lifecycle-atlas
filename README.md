# Scientific Data Lifecycle Atlas

This repository contains Lifecycle Atlas v1.2 as a standalone, data-driven
documentation project. The canonical lifecycle model lives under
`knowledge/lifecycle-atlas/`; the static site under `docs/lifecycle-atlas/`
is generated from that model.

The repository does not contain the MOF Scientific Data Platform runtime.
Consequently, its project mapping remains specification-oriented until real
platform test evidence is imported from the platform repository. Atlas
contract tests are not treated as platform runtime evidence.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python scripts/validate_lifecycle_atlas.py
.venv/bin/python scripts/build_lifecycle_atlas.py --check
.venv/bin/python -m pytest -q tests/test_lifecycle_atlas_contract.py
```

After knowledge JSON changes, rebuild the generated browser asset with:

```bash
.venv/bin/python scripts/build_lifecycle_atlas.py
```

The larger platform repository can link to this repository directly or pin it
as a Git submodule. Runtime evidence must always be produced by an observed
platform test run at a concrete commit; never infer it from this Atlas repo's
own contract tests.

## Runtime evidence contract

`knowledge/lifecycle-atlas/runtime_evidence.json` is optional and is not
present in this repository yet. When a platform run supplies it, the validator
requires a concrete platform commit SHA, a UTC timestamp, the observed pytest
summary, and one result record for every mapped lifecycle stage. A
`project_mapping.json` status may become `evidence-backed` only when that
stage's evidence record contains at least one observed passing test. The
validator deliberately continues to reject the stronger `verified` claim.
