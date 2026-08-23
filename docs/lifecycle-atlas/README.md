# Scientific Data Lifecycle Atlas — Repository Integration

This directory contains the generated interactive Atlas.

**Do not edit `assets/atlas-data.js` directly.**

The source of truth lives in:

```text
knowledge/lifecycle-atlas/
```

Rebuild:

```bash
python scripts/build_lifecycle_atlas.py
```

Validate:

```bash
python scripts/validate_lifecycle_atlas.py
```

Check that committed generated data is current:

```bash
python scripts/build_lifecycle_atlas.py --check
```

Run the contract tests:

```bash
pytest -q tests/test_lifecycle_atlas_contract.py
```

Open locally by serving the repository root with any simple HTTP server, for example:

```bash
python -m http.server 8080
```

Then browse to:

```text
http://localhost:8080/docs/lifecycle-atlas/
```

## Trust model

The Atlas has three evidence levels:

- external standards/evidence;
- explicit synthesis;
- repository-specific decisions.

Runtime implementation remains unverified until the repository tests and demo are actually executed.
