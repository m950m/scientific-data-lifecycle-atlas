#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, json, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge/lifecycle-atlas"
OUT = ROOT / "docs/lifecycle-atlas/assets/atlas-data.js"
RUNTIME_EVIDENCE = K / "runtime_evidence.json"

FILES = {
    "methodology":"methodology.json",
    "stages":"stages.json",
    "failures":"failures.json",
    "standards":"standards.json",
    "metrics":"metrics.json",
    "materials_lens":"materials_lens.json",
    "documented_cases":"documented_cases.json",
    "sources":"sources.json",
    "project_sources":"project_sources.json",
    "claims":"claims.json",
    "project_mapping":"project_mapping.json",
    "project_case":"case_studies/sample_mof_001.json",
}

ATLAS_VERSION = "1.2"

def content_last_updated() -> str:
    """Derive a real 'last updated' timestamp instead of a hardcoded literal.

    Previously this was the fixed string "2026-08-23" baked into source —
    every future rebuild would print that same date forever, silently going
    stale regardless of actual content changes. Use the git commit history
    of the knowledge files: deterministic across any clone/checkout of the
    real repository, since git preserves the *commit* date, not checkout
    time. Deliberately do NOT fall back to filesystem mtime — mtimes differ
    across fresh clones/extractions and would make `--check` spuriously
    fail. Outside a git checkout (e.g. a bare extracted pack), report the
    limitation honestly rather than fabricating a plausible-looking date.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(K.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, timeout=5, check=False,
        )
        ts = result.stdout.strip()
        if ts:
            return ts
    except Exception:
        pass
    return "unknown (not a git checkout - run inside the integrated repository for an accurate value)"

def load():
    data = {
        "atlas_version": ATLAS_VERSION,
        "updated": content_last_updated(),
    }
    for key, rel in FILES.items():
        data[key] = json.loads((K / rel).read_text(encoding="utf-8"))
    if RUNTIME_EVIDENCE.exists():
        data["runtime_evidence"] = json.loads(
            RUNTIME_EVIDENCE.read_text(encoding="utf-8")
        )
    return data

def render(data):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "/* GENERATED FILE — DO NOT EDIT. Edit knowledge/lifecycle-atlas/*.json and rebuild. */\nwindow.ATLAS_DATA=" + payload + ";\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Fail if generated asset is stale.")
    args = ap.parse_args()
    text = render(load())
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("ERROR: docs/lifecycle-atlas/assets/atlas-data.js is stale. Run scripts/build_lifecycle_atlas.py", file=sys.stderr)
            return 1
        print("OK: generated atlas data is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
