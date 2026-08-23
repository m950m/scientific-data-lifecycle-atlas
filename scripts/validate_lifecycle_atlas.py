#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge/lifecycle-atlas"
SCHEMA_PATH = K / "schema/atlas_bundle.schema.json"
RUNTIME_EVIDENCE_PATH = K / "runtime_evidence.json"

def read(rel):
    return json.loads((K / rel).read_text(encoding="utf-8"))

def check_schema(bundle, errors):
    """Validate the assembled bundle against schema/atlas_bundle.schema.json.

    This was previously shipped but never wired into validation or CI —
    a schema file with no enforcement is dead weight. Fails loudly (not
    silently skips) if jsonschema is missing, since an unenforced schema
    is the exact failure mode this function exists to close.
    """
    try:
        import jsonschema
    except ImportError:
        fail(
            "jsonschema is not installed but schema/atlas_bundle.schema.json "
            "is part of this contract. Add 'jsonschema' to the project's "
            "dependencies (pyproject.toml) and `pip install jsonschema`.",
            errors,
        )
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    v = validator_cls(schema, format_checker=jsonschema.FormatChecker())
    for err in sorted(v.iter_errors(bundle), key=str):
        fail(f"schema: {err.message} (at {'/'.join(str(p) for p in err.absolute_path)})", errors)

def fail(msg, errors):
    errors.append(msg)

def unique(items, key, label, errors):
    vals = [x[key] for x in items]
    dup = sorted({v for v in vals if vals.count(v) > 1})
    if dup:
        fail(f"{label}: duplicate {key}: {dup}", errors)

def load_runtime_evidence(errors):
    """Load observed platform evidence only when a producer has supplied it."""
    if not RUNTIME_EVIDENCE_PATH.exists():
        return None
    try:
        return json.loads(RUNTIME_EVIDENCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"runtime_evidence: cannot read valid JSON: {exc}", errors)
        return None

def validate_runtime_evidence(evidence, stage_ids, errors):
    """Cross-check evidence semantics that JSON Schema alone cannot express."""
    if not isinstance(evidence, dict):
        return {}

    results = evidence.get("stage_results")
    if not isinstance(results, list):
        return {}

    rows_by_stage = {}
    duplicate_ids = set()
    for row in results:
        if not isinstance(row, dict):
            continue
        stage_id = row.get("stage_id")
        if not isinstance(stage_id, str):
            continue
        if stage_id in rows_by_stage:
            duplicate_ids.add(stage_id)
        else:
            rows_by_stage[stage_id] = row

    if duplicate_ids:
        fail(f"runtime_evidence: duplicate stage_id values: {sorted(duplicate_ids)}", errors)
    unknown_ids = sorted(
        str(stage_id) for stage_id in rows_by_stage
        if stage_id not in stage_ids
    )
    if unknown_ids:
        fail(f"runtime_evidence: unknown stage_id values: {unknown_ids}", errors)
    missing_ids = sorted(stage_ids - set(rows_by_stage))
    if missing_ids:
        fail(f"runtime_evidence: missing stage_id values: {missing_ids}", errors)

    for stage_id, row in rows_by_stage.items():
        tests = row.get("tests")
        if not isinstance(tests, list):
            continue

        outcomes_by_nodeid = {}
        duplicate_nodeids = set()
        for test in tests:
            if not isinstance(test, dict):
                continue
            nodeid = test.get("nodeid")
            if not isinstance(nodeid, str):
                continue
            if nodeid in outcomes_by_nodeid:
                duplicate_nodeids.add(nodeid)
            else:
                outcomes_by_nodeid[nodeid] = test.get("outcome")
        if duplicate_nodeids:
            fail(
                f"runtime_evidence {stage_id}: duplicate test nodeids: "
                f"{sorted(str(nodeid) for nodeid in duplicate_nodeids)}",
                errors,
            )

        observed_passed = sum(
            1 for outcome in outcomes_by_nodeid.values() if outcome == "passed"
        )
        observed_failed = sum(
            1 for outcome in outcomes_by_nodeid.values() if outcome == "failed"
        )
        if row.get("passed") != observed_passed:
            fail(
                f"runtime_evidence {stage_id}: passed={row.get('passed')} does not "
                f"match {observed_passed} passed test records",
                errors,
            )
        if row.get("failed") != observed_failed:
            fail(
                f"runtime_evidence {stage_id}: failed={row.get('failed')} does not "
                f"match {observed_failed} failed test records",
                errors,
            )

        lineage = row.get("lineage")
        if isinstance(lineage, dict):
            lineage_nodeid = lineage.get("test_nodeid")
            if not isinstance(lineage_nodeid, str):
                continue
            observed_outcome = outcomes_by_nodeid.get(lineage_nodeid)
            if observed_outcome is None:
                fail(
                    f"runtime_evidence {stage_id}: lineage test_nodeid "
                    f"{lineage_nodeid!r} is not present in tests",
                    errors,
                )
            elif observed_outcome != lineage.get("result"):
                fail(
                    f"runtime_evidence {stage_id}: lineage result "
                    f"{lineage.get('result')!r} does not match test outcome "
                    f"{observed_outcome!r}",
                    errors,
                )

    test_run = evidence.get("test_run")
    if isinstance(test_run, dict):
        summary = test_run.get("summary")
        if isinstance(summary, dict) and test_run.get("exit_code") == 0:
            if summary.get("failed", 0) or summary.get("errors", 0):
                fail(
                    "runtime_evidence: exit_code=0 conflicts with failed/error "
                    "tests in the observed summary",
                    errors,
                )

    return rows_by_stage

def main():
    errors = []
    stages = read("stages.json")
    failures = read("failures.json")
    standards = read("standards.json")
    metrics = read("metrics.json")
    materials_lens = read("materials_lens.json")
    documented_cases = read("documented_cases.json")
    sources = read("sources.json")
    project_sources = read("project_sources.json")
    claims = read("claims.json")
    mapping = read("project_mapping.json")
    case = read("case_studies/sample_mof_001.json")
    methodology = read("methodology.json")
    runtime_evidence = load_runtime_evidence(errors)

    # Structural contract: the bundle actually shipped to the frontend
    # must conform to schema/atlas_bundle.schema.json. This was previously
    # unused dead weight; now it is load-bearing.
    bundle = {
        "atlas_version": "1.2",
        "updated": "1970-01-01T00:00:00+00:00",  # placeholder; build script fills the real value
        "methodology": methodology,
        "stages": stages,
        "failures": failures,
        "standards": standards,
        "metrics": metrics,
        "materials_lens": materials_lens,
        "documented_cases": documented_cases,
        "sources": sources,
        "project_sources": project_sources,
        "claims": claims,
        "project_mapping": mapping,
        "project_case": case,
    }
    if runtime_evidence is not None:
        bundle["runtime_evidence"] = runtime_evidence
    check_schema(bundle, errors)

    unique(stages, "id", "stages", errors)
    unique(failures, "id", "failures", errors)
    unique(sources, "id", "sources", errors)
    unique(project_sources, "id", "project_sources", errors)
    unique(claims, "id", "claims", errors)

    stage_ids = {x["id"] for x in stages}
    source_ids = {x["id"] for x in sources}
    project_source_ids = {x["id"] for x in project_sources}
    all_refs = source_ids | project_source_ids

    if len(stages) != 10:
        fail(f"Expected 10 operational stages, found {len(stages)}", errors)

    required_stage_fields = {"id","num","name","en","purpose","inputs","operations","outputs","failures","signals","controls","records","refs"}
    for s in stages:
        missing = required_stage_fields - set(s)
        if missing:
            fail(f"stage {s.get('id')}: missing {sorted(missing)}", errors)
        if not s.get("controls") or not s.get("records"):
            fail(f"stage {s['id']}: controls and evidence records must be non-empty", errors)
        for ref in s.get("refs", []):
            if ref not in source_ids:
                fail(f"stage {s['id']}: unknown external ref {ref}", errors)
        risk = s.get("risk")
        if not isinstance(risk, int) or not (0 <= risk <= 100):
            fail(f"stage {s['id']}: risk must be integer 0..100", errors)

    for f in failures:
        if f["root"] not in stage_ids:
            fail(f"failure {f['id']}: unknown root stage {f['root']}", errors)
        if f["root"] not in f.get("prop", []):
            fail(f"failure {f['id']}: propagation must include root stage", errors)
        for sid in f.get("prop", []):
            if sid not in stage_ids:
                fail(f"failure {f['id']}: unknown propagated stage {sid}", errors)
        for ref in f.get("refs", []):
            if ref not in source_ids:
                fail(f"failure {f['id']}: unknown external ref {ref}", errors)

    for m in metrics:
        if m.get("stage") not in stage_ids:
            fail(f"metric {m.get('name')}: unknown stage {m.get('stage')}", errors)
        if not m.get("caveat"):
            fail(f"metric {m.get('name')}: caveat required to prevent over-interpretation", errors)

    # Previously unchecked: standards.json and documented_cases.json carry
    # `refs` just like stages/failures/claims, but nothing validated them —
    # a dangling id here passed CI silently.
    for st in standards:
        for ref in st.get("refs", []):
            if ref not in source_ids:
                fail(f"standard {st.get('name')}: unknown external ref {ref}", errors)
        if not st.get("not"):
            fail(f"standard {st.get('name')}: 'not' (scope boundary) is required", errors)

    for dc in documented_cases:
        for ref in dc.get("refs", []):
            if ref not in source_ids:
                fail(f"documented_case {dc.get('title')}: unknown external ref {ref}", errors)
        if not dc.get("caution"):
            fail(f"documented_case {dc.get('title')}: caution (non-generalization note) is required", errors)

    allowed_labels = {"standard","evidence","synthesis","project_decision","hypothesis"}
    for c in claims:
        if c.get("label") not in allowed_labels:
            fail(f"claim {c['id']}: invalid epistemic label {c.get('label')}", errors)
        if not c.get("caveat"):
            fail(f"claim {c['id']}: caveat is required", errors)
        for ref in c.get("refs", []):
            if ref not in all_refs:
                fail(f"claim {c['id']}: unknown ref {ref}", errors)
        if c.get("label") == "hypothesis" and c.get("confidence") == "high":
            fail(f"claim {c['id']}: hypothesis must not be marked high confidence", errors)

    coverage = mapping.get("stage_coverage", [])
    coverage_ids = [x.get("stage_id") for x in coverage]
    if set(coverage_ids) != stage_ids or len(coverage_ids) != len(stage_ids):
        fail("project_mapping: must contain exactly one coverage record per operational stage", errors)
    evidence_rows = validate_runtime_evidence(runtime_evidence, stage_ids, errors)
    allowed_status = {"specified","bounded_demo","partial","local_only","evidence-backed"}
    for row in coverage:
        if row.get("status") not in allowed_status:
            fail(f"project_mapping {row.get('stage_id')}: unsupported status {row.get('status')}", errors)
        if row.get("status") == "evidence-backed":
            stage_id = row.get("stage_id")
            evidence_row = evidence_rows.get(stage_id)
            evidence_tests = (
                evidence_row.get("tests", [])
                if isinstance(evidence_row, dict)
                and isinstance(evidence_row.get("tests", []), list)
                else []
            )
            passed_tests = [
                test for test in evidence_tests
                if isinstance(test, dict) and test.get("outcome") == "passed"
            ]
            passed_count = (
                evidence_row.get("passed", 0)
                if isinstance(evidence_row, dict)
                and isinstance(evidence_row.get("passed", 0), int)
                else 0
            )
            if runtime_evidence is None:
                fail(
                    f"project_mapping {stage_id}: evidence-backed requires "
                    "knowledge/lifecycle-atlas/runtime_evidence.json",
                    errors,
                )
            elif not evidence_row or passed_count < 1 or not passed_tests:
                fail(
                    f"project_mapping {stage_id}: evidence-backed requires at "
                    "least one recorded passed test",
                    errors,
                )
        if not row.get("gap"):
            fail(f"project_mapping {row.get('stage_id')}: explicit gap is required", errors)

    if case.get("scientific_status") != "synthetic_or_illustrative_not_a_research_finding":
        fail("project case must remain explicitly labeled illustrative, not a research finding", errors)
    for j in case.get("journey", []):
        if j.get("stage_id") not in stage_ids:
            fail(f"project case journey: unknown stage {j.get('stage_id')}", errors)
        if j.get("runtime_verification") == "verified":
            fail("project case must not claim runtime verification; use evidence-backed project mapping with runtime evidence", errors)
    for fi in case.get("failure_injections", []):
        if fi.get("stage_id") not in stage_ids:
            fail(f"failure injection {fi.get('id')}: unknown stage {fi.get('stage_id')}", errors)
        if not fi.get("minimum_test"):
            fail(f"failure injection {fi.get('id')}: minimum_test required", errors)

    for s in sources:
        url = s.get("url","")
        if not url.startswith("https://"):
            fail(f"source {s['id']}: external source URL must be https://", errors)

    if errors:
        print("LIFECYCLE ATLAS VALIDATION FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print("LIFECYCLE ATLAS VALIDATION PASSED")
    print(f" stages={len(stages)} failures={len(failures)} claims={len(claims)} external_sources={len(sources)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
