from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge/lifecycle-atlas"

def load(name):
    return json.loads((K / name).read_text(encoding="utf-8"))

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def isolated_validator_repo(tmp_path):
    repo = tmp_path / "atlas"
    shutil.copytree(K, repo / "knowledge/lifecycle-atlas")
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(
        ROOT / "scripts/validate_lifecycle_atlas.py",
        repo / "scripts/validate_lifecycle_atlas.py",
    )
    return repo

def run_validator(repo):
    return subprocess.run(
        [sys.executable, str(repo / "scripts/validate_lifecycle_atlas.py")],
        cwd=repo,
        text=True,
        capture_output=True,
    )

def runtime_evidence_fixture(repo, evidence_stage="ingest"):
    mapping = json.loads(
        (repo / "knowledge/lifecycle-atlas/project_mapping.json").read_text(
            encoding="utf-8"
        )
    )
    results = []
    for row in mapping["stage_coverage"]:
        tests = []
        if row["stage_id"] == evidence_stage:
            tests = [
                {
                    "nodeid": "tests/test_runtime_fixture.py::test_observed_behavior",
                    "outcome": "passed",
                }
            ]
        results.append(
            {
                "stage_id": row["stage_id"],
                "passed": len(tests),
                "failed": 0,
                "tests": tests,
            }
        )
    return {
        "schema_version": "1.0",
        "repository": "mof-platform-validator-test-fixture",
        "commit_sha": "a" * 40,
        "timestamp": "2026-08-23T12:00:00Z",
        "test_run": {
            "command": "pytest -q src/mof_platform",
            "exit_code": 0,
            "duration_seconds": 1.25,
            "summary": {
                "passed": 1,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
        },
        "stage_results": results,
    }

def mark_stage_evidence_backed(repo, stage_id="ingest"):
    mapping_path = repo / "knowledge/lifecycle-atlas/project_mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    row = next(
        row for row in mapping["stage_coverage"] if row["stage_id"] == stage_id
    )
    row["status"] = "evidence-backed"
    write_json(mapping_path, mapping)

def test_contract_validator_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_lifecycle_atlas.py")],
        cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stdout + result.stderr

def test_generated_asset_is_current():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_lifecycle_atlas.py"), "--check"],
        cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"runtime_evidence"' not in (
        ROOT / "docs/lifecycle-atlas/assets/atlas-data.js"
    ).read_text(encoding="utf-8")

def test_every_stage_has_project_coverage_and_explicit_gap():
    stage_ids = {s["id"] for s in load("stages.json")}
    rows = load("project_mapping.json")["stage_coverage"]
    assert {r["stage_id"] for r in rows} == stage_ids
    assert all(r["gap"].strip() for r in rows)

def test_project_case_never_claims_research_finding():
    case = load("case_studies/sample_mof_001.json")
    assert case["scientific_status"] == "synthetic_or_illustrative_not_a_research_finding"
    assert all(j["runtime_verification"] != "verified" for j in case["journey"])

def test_epistemic_labels_are_explicit():
    allowed = {"standard","evidence","synthesis","project_decision","hypothesis"}
    claims = load("claims.json")
    assert claims
    assert all(c["label"] in allowed for c in claims)
    assert all(c["caveat"].strip() for c in claims)

def test_evidence_backed_status_requires_runtime_evidence(tmp_path):
    repo = isolated_validator_repo(tmp_path)
    mark_stage_evidence_backed(repo)

    result = run_validator(repo)

    assert result.returncode == 1
    assert "evidence-backed requires knowledge/lifecycle-atlas/runtime_evidence.json" in result.stdout

def test_valid_optional_runtime_evidence_can_back_a_stage(tmp_path):
    repo = isolated_validator_repo(tmp_path)
    mark_stage_evidence_backed(repo)
    evidence = runtime_evidence_fixture(repo)
    write_json(repo / "knowledge/lifecycle-atlas/runtime_evidence.json", evidence)

    result = run_validator(repo)

    assert result.returncode == 0, result.stdout + result.stderr

def test_runtime_evidence_counts_match_test_records(tmp_path):
    repo = isolated_validator_repo(tmp_path)
    mark_stage_evidence_backed(repo)
    evidence = runtime_evidence_fixture(repo)
    ingest = next(
        row for row in evidence["stage_results"] if row["stage_id"] == "ingest"
    )
    ingest["passed"] = 2
    write_json(repo / "knowledge/lifecycle-atlas/runtime_evidence.json", evidence)

    result = run_validator(repo)

    assert result.returncode == 1
    assert "does not match 1 passed test records" in result.stdout

def test_runtime_evidence_covers_every_mapped_stage(tmp_path):
    repo = isolated_validator_repo(tmp_path)
    evidence = runtime_evidence_fixture(repo)
    removed = evidence["stage_results"].pop()
    write_json(repo / "knowledge/lifecycle-atlas/runtime_evidence.json", evidence)

    result = run_validator(repo)

    assert result.returncode == 1
    assert f"missing stage_id values: ['{removed['stage_id']}']" in result.stdout

def test_runtime_evidence_timestamp_must_be_utc(tmp_path):
    repo = isolated_validator_repo(tmp_path)
    evidence = runtime_evidence_fixture(repo)
    evidence["timestamp"] = "2026-08-23T15:00:00+03:00"
    write_json(repo / "knowledge/lifecycle-atlas/runtime_evidence.json", evidence)

    result = run_validator(repo)

    assert result.returncode == 1
    assert "schema:" in result.stdout
    assert "timestamp" in result.stdout

def test_lineage_result_references_an_observed_test(tmp_path):
    repo = isolated_validator_repo(tmp_path)
    evidence = runtime_evidence_fixture(repo)
    ingest = next(
        row for row in evidence["stage_results"] if row["stage_id"] == "ingest"
    )
    ingest["lineage"] = {
        "result": "passed",
        "test_nodeid": "tests/test_runtime_fixture.py::test_missing_lineage",
        "observed_chain": ["observation", "source"],
    }
    write_json(repo / "knowledge/lifecycle-atlas/runtime_evidence.json", evidence)

    result = run_validator(repo)

    assert result.returncode == 1
    assert "is not present in tests" in result.stdout

def test_standalone_user_service_is_restartable_and_points_to_this_checkout():
    service_script = ROOT / "scripts/manage_user_service.py"
    spec = importlib.util.spec_from_file_location("manage_user_service", service_script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    unit = module.render_unit("127.0.0.1", 8000)

    assert f"WorkingDirectory={ROOT}" in unit
    assert str(ROOT / "scripts/serve_lifecycle_atlas.py") in unit
    assert "Restart=always" in unit
    assert "NoNewPrivileges=true" in unit
    assert "ProtectHome=read-only" in unit

def test_independent_deployment_contract_is_pinned_and_publishable():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/lifecycle-atlas.yml").read_text(
        encoding="utf-8"
    )

    assert "nginx-unprivileged:1.30.4-alpine3.24@sha256:" in dockerfile
    assert "COPY docs/lifecycle-atlas/ /usr/share/nginx/html/" in dockerfile
    assert "restart: unless-stopped" in compose
    assert "actions/upload-pages-artifact@v4" in workflow
    assert "path: docs/lifecycle-atlas" in workflow
