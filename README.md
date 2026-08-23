# Scientific Data Lifecycle Atlas

This repository contains Lifecycle Atlas v1.2.1 as a standalone, data-driven
documentation project. The canonical lifecycle model lives under
`knowledge/lifecycle-atlas/`; the static site under `docs/lifecycle-atlas/`
is generated from that model. All authoritative knowledge content and the
public interface are maintained in English.

The repository does not contain the MOF Scientific Data Platform runtime.
Consequently, its project mapping remains specification-oriented until real
platform test evidence is imported from the platform repository. Atlas
contract tests are not treated as platform runtime evidence.

## Run independently with Docker

The container runs in the background and uses a restart policy, so it remains
available after the terminal closes and restarts with the Docker daemon unless
it was explicitly stopped.

```bash
docker compose up --build --detach
docker compose ps
```

Open <http://localhost:8000>. The health endpoint is
<http://localhost:8000/healthz>. To inspect or stop it:

```bash
docker compose logs --follow
docker compose down
```

Copy `.env.example` to `.env` only when a different bind address or port is
needed. The default bind address is loopback-only; public access should use
GitHub Pages or an authenticated TLS reverse proxy.

If Docker daemon access is unavailable, install the equivalent persistent user
service without root privileges:

```bash
.venv/bin/python scripts/manage_user_service.py install
.venv/bin/python scripts/manage_user_service.py status
.venv/bin/python scripts/manage_user_service.py logs
```

The service starts with the user's systemd session and restarts on failure. To
remove it later, run:

```bash
.venv/bin/python scripts/manage_user_service.py remove
```

## Publish as an independent reference

The canonical source is the
[GitHub repository](https://github.com/m950m/scientific-data-lifecycle-atlas),
and the public [interactive Atlas](https://m950m.github.io/scientific-data-lifecycle-atlas/)
is published from `docs/lifecycle-atlas/` after a successful validation run on
`main`.

Use the hosted URL for reading, and pin the source tag plus full commit SHA when
the larger platform cites the Atlas. See [REFERENCE.md](REFERENCE.md) for a
copy-ready reference record and the claim boundary.

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
