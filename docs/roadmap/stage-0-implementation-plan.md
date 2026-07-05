# Stage 0 Implementation Plan

Stage 0 builds the QA Control Layer before AI Coding scale-up.

## Stage 0A - Framework Validation Foundation

Goal:

```text
Make the framework capable of rejecting invalid, unsafe, or non-approved generated artifacts before runtime execution.
```

Deliverables:

```text
artifact metadata schema
artifact state lifecycle rules
approval_record.yaml schema
Test Case DSL schema
Provider Contract schema
Provider Instance schema
Execution Profile schema
Environment Binding schema
Suite Manifest schema
regress validate
secret guardrail
validation error taxonomy
```

Definition of done:

```text
invalid schema -> regress validate fails with owner_action
raw secret in artifact -> regress validate fails
generated_requires_review artifact -> regress run rejects release execution
approved_for_regression requires approval_record.yaml
approval_record artifact hash mismatch -> regress run fails
```

## Stage 0B - Dry-run Planner and Readiness Report

Goal:

```text
Make the framework able to determine readiness without touching runtime dependencies.
```

Deliverables:

```text
regress run --dry-run
cross-artifact reference validation
target resolution validation
operation / bind_as validation
dry_run_readiness_report.yaml
owner-actionable error messages
```

Definition of done:

```text
dry-run does not start DB/NATS/WireMock/external calls
missing provider binding appears in dry_run_readiness_report.yaml
unsupported operation appears with owner_action
non-approved artifact blocks readiness
dry-run exits 0 only when execution readiness checks pass
```

## Stage 0C - QA Agent MVP

Goal:

```text
Make QA Agent draft useful, reviewable test artifacts and repair non-business validation errors.
```

Deliverables:

```text
release_testing_input.yaml template
spec_gap_report.yaml
proposed_ac.yaml
assumption_log.yaml
open_questions.md
release_test_plan.yaml
seed_test_case.yaml
data_setup_plan.yaml
framework artifact drafts
review_pack/
validate/dry-run repair loop
```

Definition of done:

```text
QA Agent can generate review pack from minimum input
QA Agent marks all assumptions as proposed_requires_review
QA Agent can run regress validate
QA Agent can run regress run --dry-run
QA Agent can repair non-business artifact errors
QA Agent cannot approve expected result
QA Agent cannot approve cleanup order
QA Agent cannot approve release recommendation
```

## AI Coding Scale-up Gate

AI Coding may scale only after Stage 0A, 0B, and 0C are proven against at least one real release.

If any Stage 0 gate fails, AI Coding may continue only in limited pilot mode.
