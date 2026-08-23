# Lifecycle Atlas Knowledge Model

These JSON files are the human-reviewable source of truth.

- `stages.json`: operational lifecycle stages.
- `failures.json`: failure taxonomy and propagation.
- `standards.json`: standards/framework role boundaries.
- `metrics.json`: proposed operational quality gates with caveats.
- `sources.json`: external primary/authoritative sources.
- `project_sources.json`: local repository specifications.
- `claims.json`: epistemic claim registry.
- `project_mapping.json`: lifecycle → repository contract mapping.
- `case_studies/sample_mof_001.json`: end-to-end illustrative record and failure-injection contract.

The frontend data file is generated from these files. CI fails if the generated artifact drifts from the knowledge model.
