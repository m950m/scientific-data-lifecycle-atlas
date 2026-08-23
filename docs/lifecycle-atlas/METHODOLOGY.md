# Lifecycle Atlas Methodology

## Purpose

The Atlas is not a second product. It is the **living scientific specification and evidence map** for the MOF Scientific Data Platform.

Its job is to answer, for every lifecycle transition:

1. What enters?
2. What operation is permitted?
3. What leaves?
4. What can fail?
5. How is the failure detected?
6. What control limits the failure?
7. What evidence must remain so another person can audit the result?
8. Which statements come from standards/evidence, which are synthesis, and which are project decisions?

## Backbone vs synthesis

- **Backbone:** NIST RDaF 2.0.
- **Complementary reference layers:** DCC Curation Lifecycle, FAIR, W3C PROV, OAIS, PREMIS, DataCite, NDSA, CoreTrustSeal/TRUST, NASEM, VIM and materials-domain infrastructure.
- **Operational decomposition:** the ten Atlas stages are an implementation synthesis. They are not presented as a new universal standard.

## Epistemic labels

| Label | Meaning | Required evidence |
|---|---|---|
| `standard` | Normative/authoritative model or specification claim | external primary source |
| `evidence` | Empirical documented observation | peer-reviewed or equivalent evidence |
| `synthesis` | Reasoned integration of multiple sources | refs + explicit caveat |
| `project_decision` | Repository-specific invariant/contract | project specification |
| `hypothesis` | Claim that still needs evaluation | explicit uncertainty and test/evaluation plan |

## Non-negotiable discipline

- Do not turn a project decision into a universal scientific fact.
- Do not turn a documentation contract into runtime evidence.
- Do not call the illustrative bundled sample a research result.
- Do not report a quality metric without its denominator, scope, and limitation.
- Do not claim preservation from backup alone.
- Do not claim scientific validity from FAIRness, schema validity, checksums, or repository certification alone.
