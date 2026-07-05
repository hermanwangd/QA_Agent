# QA Agent Operating Model

## Core Boundary

```text
Product Spec defines truth.
QA Agent drafts and analyzes.
Framework validates contracts and dry-run readiness.
Human Release Quality Owner approves business truth and release readiness.
```

## Non-Negotiable Rules

```text
Framework must not infer business truth.
QA Agent must not silently convert assumptions into expected results.
QA Agent must not approve generated artifacts.
Human approval must not be bypassable by CLI flag.
Framework run must reject non-approved artifacts for release evidence.
Raw secrets must be blocked before evidence/report publication.
Dry-run must not invoke provider runtime.
```

## Roles

| Role | Responsibility |
|---|---|
| Product / RP Owner | Owns release change brief, AC, business rules, data contracts, and interface contracts. |
| QA Release Testing Agent | Drafts release test scope, spec gaps, seed cases, data setup plans, framework artifacts, and review packs. |
| Framework Validation Layer | Validates schemas, references, artifact state, secret guardrails, and dry-run readiness. |
| Human Release Quality Owner | Approves AC interpretation, expected results, data safety, cleanup safety, and release testing recommendation. |

## Artifact State Lifecycle

```text
draft
  -> generated_requires_review
  -> reviewed
  -> approved_for_regression
  -> executed
  -> retired / updated
```

Rules:

```text
QA Agent can create draft, generated_requires_review, and proposed_requires_review only.
Human Release Quality Owner is required for approved_for_regression.
Framework release evidence can use only approved_for_regression artifacts.
Framework run must reject generated_requires_review artifacts for release evidence.
```

## RACI

| Activity | Product / RP Owner | QA Agent | Framework | Human Release Quality Owner |
|---|---|---|---|---|
| Provide release change brief | A/R | C | I | C |
| Interpret AC/business rule | A/R | C | I | A/R |
| Detect spec gaps | C | R | I | A |
| Propose AC clarification | C | R | I | A |
| Draft release test plan | C | R | I | A |
| Draft data setup plan | C | R | I | A |
| Validate artifact schema | I | C | R | I |
| Dry-run readiness check | I | C | R | I |
| Repair non-business artifact errors | I | R | C | I |
| Approve expected results | C | I | I | A/R |
| Approve cleanup safety | C | I | I | A/R |
| Approve regression execution | C | I | C | A/R |
| Produce release evidence | I | C | R | A |

Legend:

```text
A = Accountable
R = Responsible
C = Consulted
I = Informed
```
