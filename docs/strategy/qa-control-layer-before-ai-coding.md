# Proposal: Build QA Control Layer Before Scaling AI Coding

Date: 2026-07-05 Asia/Taipei

Status: Enhanced proposal for implementation planning

Owner: Product / Engineering / Release Quality

## 1. Executive Summary

The team currently has no dedicated QA role. The primary lifecycle bottleneck is therefore not coding speed, but release quality validation capability.

Scaling AI Coding before establishing release validation controls will amplify risk:

```text
more code changes
-> faster codebase churn
-> regression coverage cannot keep up
-> test data preparation becomes inconsistent
-> failure triage becomes harder
-> release evidence diverges by team/person
-> release quality risk increases
```

Decision:

```text
Do not scale AI Coding until the QA Control Layer reaches the QA Readiness Gate.
```

The QA Control Layer has two required parts:

```text
1. QA Release Testing Agent
2. Minimum Framework Validation Layer
```

Operating principle:

```text
Product Spec defines truth.
QA Release Testing Agent drafts and analyzes.
Framework validates contracts and dry-run readiness.
Human Release Quality Owner approves business truth and release readiness.
AI Coding may scale only after QA readiness is proven.
```

## 2. Problem Statement

The current lifecycle lacks:

```text
dedicated QA ownership
standardized release testing process
test data lifecycle control
consistent evidence format
artifact state lifecycle
AI-generated artifact guardrails
repeatable dry-run readiness validation
release approval audit trail
```

AI Coding improves throughput, but without a QA Control Layer it also increases the speed at which low-confidence changes reach the codebase.

The correct sequence is:

```text
QA Control Layer -> controlled AI Coding scale-up
```

This is not a delay strategy. It is a release-risk control strategy.

## 3. Scope

### In Scope

- Product / RP minimum input template
- QA Agent rules for drafting, spec-gap detection, artifact generation, and repair
- Framework validation and dry-run layer
- Artifact state lifecycle
- Human approval workflow
- Release test review pack
- Secret and data safety guardrails
- Readiness gate before AI Coding scale-up

### Out of Scope for Stage 0

- Full runtime execution engine
- Performance testing
- Fault injection
- k6 workload approval
- Autonomous business expected-result approval
- Autonomous release approval
- AI Coding rollout itself

## 4. Non-Negotiable Control Rules

```text
Framework must not infer business truth.
QA Agent must not silently convert assumptions into expected results.
QA Agent must not approve generated artifacts.
Human approval must not be bypassable by CLI flag.
Framework run must reject non-approved artifacts for release evidence.
Raw secrets must be blocked before evidence/report publication.
Dry-run must not invoke provider runtime.
```

## 5. Role Model and RACI

| Activity | Product / RP Owner | QA Release Testing Agent | Framework Validation Layer | Human Release Quality Owner |
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

Human Release Quality Owner can be:

```text
Product Owner
Tech Lead
Release Owner
Domain Expert
Temporary QA Owner
```

The model must not assume a dedicated QA Lead exists.

## 6. Target Operating Model

```text
Product / RP minimum input
        |
        v
QA Release Testing Agent intake
        |
        v
Spec gap detection
        |
        v
Release test scope draft
        |
        v
Seed test case + data setup plan draft
        |
        v
Framework artifact draft
        |
        v
regress validate
        |
        v
regress run --dry-run
        |
        v
QA Agent repair loop for non-business errors
        |
        v
Review pack generation
        |
        v
Human Release Quality Owner approval
        |
        v
approved_for_regression
        |
        v
Framework run
        |
        v
Evidence package + release test report
```

## 7. Minimum Product / RP Input Package

The initial input package must be small enough to adopt, but structured enough to drive traceability.

Required file:

```text
release_testing_input.yaml
```

Required metadata:

```yaml
input_version: v0.1
release_id: REL-YYYYMMDD-001
source_ref:
  spec_doc: docs/product/spec.md
  change_ticket: JIRA-123
owner:
  product_owner: ""
  tech_owner: ""
  release_quality_owner: ""
last_updated_at: "2026-07-05T00:00:00+08:00"
```

### 7.1 Release Change Brief

```yaml
release_change:
  changed_features:
    - feature_id: ""
      summary: ""
  changed_acceptance_criteria:
    - ac_id: ""
  changed_components:
    - component: ""
  known_risks:
    - risk_id: ""
      description: ""
      severity: P0
  must_test_flows:
    - flow_id: ""
      reason: ""
```

### 7.2 Acceptance Criteria / Spec

```yaml
acceptance_criteria:
  - ac_id: AC-001
    priority: P0
    given: ""
    when: ""
    then: ""
    business_rule: ""
    expected_result: ""
    error_behavior: ""
    source_ref: ""
```

### 7.3 Test Data Contract

```yaml
test_data_contract:
  reference_tables:
    - table: ""
      access: read_only
  seed_tables:
    - table: ""
      seed_strategy: insert_new_rows
  verify_tables:
    - table: ""
      verification_hint: ""
  cleanup:
    order:
      - table: ""
    safety_rule: delete_by_test_run_id_only
  forbidden_mutations:
    - table: ""
  open_questions:
    - question: ""
```

### 7.4 Interface / Dependency Contract

```yaml
interface_contract:
  apis:
    - name: ""
      method: POST
      path: ""
      request_schema_ref: ""
      response_schema_ref: ""
  events:
    - provider: nats
      subject: ""
      payload_schema_ref: ""
  dependencies:
    - provider: wiremock
      behavior: ""
      stub_required: true
  db_verification_hints:
    - query_ref: ""
```

## 8. QA Release Testing Agent MVP

The QA Agent MVP drafts and analyzes. It does not approve business truth.

### 8.1 Required Outputs

```text
spec_gap_report.yaml
proposed_ac.yaml
assumption_log.yaml
open_questions.md
release_test_plan.yaml
seed_test_case.yaml
data_setup_plan.yaml
test_case.yaml
suite_manifest.yaml
provider_instance.yaml
execution_profile.yaml
environment_binding.yaml
review_pack/
```

### 8.2 Spec Gap Detection Rules

If AC/spec input is incomplete, the agent must not invent truth.

It must produce:

```yaml
spec_gap_report:
  release_id: REL-YYYYMMDD-001
  gaps:
    - gap_id: GAP-001
      source_ac_id: AC-001
      gap_type: missing_expected_result
      impact: cannot_generate_approved_expected_result
      owner_action: Product owner must define expected result.
```

All inferred content must be marked:

```yaml
state: proposed_requires_review
assumption_source: qa_agent_inference
requires_human_approval: true
```

### 8.3 Agent Repair Rules

The QA Agent may automatically repair non-business artifact issues:

```text
missing provider instance file
missing environment binding file
invalid artifact reference path
unsupported operation mapping if canonical mapping is known
wrong bind_as when schema contract is explicit
missing SQL parameter placeholder
invalid evidence ref
missing expected result reference file
schema violation
```

The QA Agent must not automatically repair or approve:

```text
business expected result value
cleanup order
unknown table dependency
fault fallback behavior
k6 threshold
secret_ref value
data safety exception
release testing recommendation
```

Clarification:

```text
"missing expected result" auto-repair means fixing a missing reference, file path, schema wrapper, or artifact state.
It does not mean inventing the expected business value.
```

## 9. Minimum Framework Validation Layer

The framework validates artifact contracts and dry-run readiness. It must remain product-agnostic.

### 9.1 Required Capabilities

```text
Test Case DSL schema validation
Provider Contract schema validation
Provider Instance schema validation
Execution Profile schema validation
Environment Binding schema validation
Suite Manifest schema validation
Artifact state validation
Secret guardrail
Cross-artifact reference validation
Validation error taxonomy
regress validate
regress run --dry-run
Dry-run execution readiness report
Owner-actionable error messages
```

### 9.2 Dry-run Must Check

```text
suite exists
test case exists
provider contract exists
provider instance exists
execution profile exists
environment binding exists
target refs resolvable
operation supported
bind_as supported
output refs valid
expected result refs valid
evidence refs valid
raw secrets blocked
artifact state valid
approval state valid
```

### 9.3 Dry-run Must Not Do

```text
must not start provider runtime
must not connect DB
must not connect NATS
must not start WireMock
must not call external service
must not produce release evidence
must not approve artifact
```

### 9.4 Dry-run Output Contract

Required file:

```text
dry_run_readiness_report.yaml
```

Minimum schema:

```yaml
dry_run_report_version: v0.1
release_id: REL-YYYYMMDD-001
suite_id: SUITE-001
status: blocked
ready_for_human_review: false
ready_for_regression_execution: false
artifact_state_status:
  status: failed
  findings:
    - artifact: test_case.yaml
      state: generated_requires_review
      required_state_for_run: approved_for_regression
reference_status:
  unresolved_refs:
    - ref: expected_results/order_created.json
      owner_action: Add expected result artifact or mark as proposed_requires_review.
provider_status:
  missing_bindings:
    - provider_id: payment-api
      binding_key: base_url
      owner_action: Add environment binding for payment-api.base_url.
operation_status:
  unsupported_operations: []
secret_guardrail:
  status: passed
  findings: []
owner_action_summary:
  - Approve expected result before execution.
  - Add missing environment binding.
```

## 10. Artifact State Lifecycle

All AI-generated artifacts must follow this lifecycle:

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

Minimum artifact metadata:

```yaml
artifact_metadata:
  artifact_id: TC-001
  artifact_type: test_case
  artifact_version: 1
  state: generated_requires_review
  generated_by: qa_release_testing_agent
  generated_at: "2026-07-05T00:00:00+08:00"
  source_refs:
    - release_testing_input.yaml#acceptance_criteria[AC-001]
  assumptions:
    - assumption_id: ASM-001
      state: proposed_requires_review
  approval_ref: null
```

## 11. Human Approval Gates

Human Release Quality Owner must approve:

```text
AC interpretation
expected result
data setup safety
cleanup safety
unknown table dependency resolution
generated artifacts moving to approved_for_regression
release test recommendation
```

Required approval artifact:

```text
approval_record.yaml
```

Minimum schema:

```yaml
approval_record_version: v0.1
approval_id: APR-001
release_id: REL-YYYYMMDD-001
approved_by:
  name: ""
  role: Human Release Quality Owner
approved_at: "2026-07-05T00:00:00+08:00"
approval_scope:
  - ac_interpretation
  - expected_result
  - data_setup_cleanup
  - approved_for_regression
approved_artifacts:
  - artifact_id: TC-001
    artifact_path: test_case.yaml
    artifact_hash: sha256:...
rejected_artifacts: []
conditions:
  - condition_id: COND-001
    description: Run only in isolated test schema.
```

Framework requirement:

```text
regress run must verify approval_record.yaml and artifact hashes before producing release evidence.
```

## 12. Stage 0 Implementation Plan

Stage 0 is split into three smaller gates to avoid a large, vague MVP.

### Stage 0A - Framework Validation Foundation

Goal:

```text
Make framework capable of rejecting invalid, unsafe, or non-approved generated artifacts before runtime execution.
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

Definition of Done:

```text
invalid schema -> regress validate fails with owner_action
raw secret in artifact -> regress validate fails
generated_requires_review artifact -> regress run rejects release execution
approved_for_regression requires approval_record.yaml
approval_record artifact hash mismatch -> regress run fails
```

### Stage 0B - Dry-run Planner and Readiness Report

Goal:

```text
Make framework able to determine readiness without touching runtime dependencies.
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

Definition of Done:

```text
dry-run does not start DB/NATS/WireMock/external calls
missing provider binding appears in dry_run_readiness_report.yaml
unsupported operation appears with owner_action
non-approved artifact blocks readiness
dry-run exits 0 only when execution readiness checks pass
```

### Stage 0C - QA Agent MVP

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

Definition of Done:

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

## 13. QA Readiness Gate Before AI Coding Scale-up

AI Coding scale-up is allowed only when all gates below pass.

| Gate | Required Evidence |
|---|---|
| Product / RP input adopted | At least one real release uses `release_testing_input.yaml`. |
| Spec gap detection works | Missing AC expected result produces `spec_gap_report.yaml`. |
| Proposed AC is review-only | `proposed_ac.yaml` uses `proposed_requires_review`. |
| Data plan exists | `data_setup_plan.yaml` includes seed, verify, cleanup, forbidden mutation. |
| Framework validate works | Invalid schema fails with owner-actionable error. |
| Dry-run works | `dry_run_readiness_report.yaml` is produced without runtime invocation. |
| Secret guardrail works | Positive/negative secret tests pass. |
| Artifact lifecycle enforced | `regress run` rejects non-approved artifacts. |
| Approval audit exists | `approval_record.yaml` is required and hash-checked. |
| Release evidence format defined | Evidence package schema is documented. |
| QA Agent cannot approve truth | Agent output never moves directly to `approved_for_regression`. |

Hard rule:

```text
If any gate fails, AI Coding may continue only in limited pilot mode, not scale-up mode.
```

## 14. Stage 1 Roadmap - Execution Foundation

Once Stage 0 passes:

```text
WireMock Runner
JDBC Runner for Oracle / DB2
NATS Runner
JSON / Schema / File Diff
Polling
Result JSON
Evidence Index
regress report
```

Goal:

```text
QA Agent generated artifacts can be human-approved and executed.
Framework can produce trusted evidence from approved artifacts only.
```

## 15. Stage 2 Roadmap - Release Quality Expansion

After Stage 0 and Stage 1 are stable:

```text
fault_scenario_plan.yaml
WireMock fault injection
fallback verification
k6 performance_test_plan.yaml
k6 external runner
failure triage assistant
release evidence summary
```

Additional human approvals:

```text
fault model approval
expected fallback behavior approval
k6 workload / threshold approval
```

## 16. Stage 3 Roadmap - AI Coding Scale-up

Only after QA Readiness Gate passes should AI Coding scale.

Governance rule:

```text
Every AI-generated code change must link to:
- updated AC/spec or explicit no-spec-change record
- generated or updated test case
- data setup plan
- validate result
- dry-run readiness result
- evidence expectation
```

AI Coding should not be measured by code output alone.

It should be measured by:

```text
code + test + data plan + dry-run readiness + release evidence quality
```

## 17. Success Metrics

### QA Agent Metrics

```text
spec gap detection rate
generated artifacts passing validate
generated artifacts passing dry-run
validation errors auto-repaired
human review acceptance rate
time saved in release test preparation
assumption leakage incidents
```

### Framework Metrics

```text
validate pass rate
dry-run pass rate
owner-actionable error rate
secret leakage incidents = 0
artifact state enforcement rate
approval hash mismatch detection rate
evidence completeness rate
cleanup safety validation rate
```

### Software Lifecycle Metrics

```text
release test preparation time reduction
P0 AC coverage visibility
regression coverage improvement
failure triage time reduction
release evidence consistency
AI coding readiness score
AI-generated code rollback rate
```

## 18. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| QA Agent invents business truth | Require `proposed_requires_review`; framework rejects unapproved artifacts. |
| Spec baseline incomplete | Generate spec gaps, proposed AC, open questions. |
| AI-generated data pollutes environment | Require data setup plan, cleanup approval, forbidden mutation list. |
| Expected result is wrong | Human approval required with artifact hash. |
| Framework becomes business engine | Framework validates contracts only; business truth remains external. |
| Approval is bypassed | `regress run` requires approval record and state check. |
| AI Coding scales too early | QA Readiness Gate blocks scale-up. |
| Scope grows too quickly | Stage 0 split into 0A/0B/0C gates. |

## 19. Final Recommendation

Approve the strategy with one condition:

```text
Treat this as an implementation program with hard gates, not as a documentation-only governance proposal.
```

Immediate next steps:

```text
1. Implement Stage 0A: Framework validation foundation.
2. Implement Stage 0B: Dry-run planner and readiness report.
3. Implement Stage 0C: QA Agent MVP and repair loop.
4. Run the QA Readiness Gate against one real release.
5. Only then approve AI Coding scale-up.
```

Final principle:

```text
QA Agent drafts.
Framework enforces contracts.
Human approves truth.
AI Coding scales only after release quality validation is under control.
```
