# Referencing the Scientific Data Lifecycle Atlas

Use the Atlas as a design and methodology reference, not as runtime evidence
for the consuming platform. A durable reference records both the release tag
and the full commit SHA; the live site URL is only the interactive view.

## Reference record for a consuming repository

After this repository has been pushed and tagged, add a file such as
`docs/references/lifecycle-atlas.md` to the consuming project:

```markdown
# Scientific Data Lifecycle Atlas reference

This project's lifecycle and evidence-mapping design was informed by the
Scientific Data Lifecycle Atlas.

## Pinned reference

- Version/tag: `v1.2.0`
- Commit: `<FULL_RELEASE_SHA>`
- Source: `https://github.com/<OWNER>/scientific-data-lifecycle-atlas/commit/<FULL_RELEASE_SHA>`
- Interactive view: `https://<OWNER>.github.io/scientific-data-lifecycle-atlas/`
- Accessed: `2026-08-24`

## Scope boundary

The Atlas is used as a design and methodology reference only. Its ten-stage
model is an operational synthesis, not a universal standard. Its contract
tests do not verify this platform, its illustrative case is not a research
finding, and its risk scores are expert-judgment rankings rather than measured
probabilities. Platform behavior and scientific validity are supported
separately by this repository's tests and runtime evidence.

## Local implementation evidence

See `<LOCAL_TEST_OR_EVIDENCE_LINK>`.
```

Resolve the immutable release commit after creating the tag with:

```bash
git rev-list -n 1 v1.2.0
```

Suggested acknowledgement:

> The lifecycle and evidence-mapping design was informed by Scientific Data
> Lifecycle Atlas v1.2.0, commit `<FULL_RELEASE_SHA>`, `<SOURCE_URL>`, accessed
> 2026-08-24. It is used as a design reference only; platform behavior and
> scientific validity are established separately by this repository's tests
> and runtime evidence.

Do not convert an Atlas contract-test result into platform runtime evidence,
and do not copy an `evidence-backed` status without the corresponding observed
platform test record.
