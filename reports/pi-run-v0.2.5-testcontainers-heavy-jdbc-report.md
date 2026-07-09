# pi-run v0.2.5 Testcontainers Heavy JDBC Report

Date: 2026-07-09 Asia/Taipei

## Scope

Validate whether project-owned Oracle Free and DB2 Testcontainers runtimes can be used to test the released framework JDBC provider in `spec-driven-auto-regression-0.2.5.jar`.

The test framework jar does not provision Oracle or DB2. This PI-run project provisions the database container, injects vendor JDBC drivers through the Maven harness, materializes a native JDBC suite, and invokes the selected framework jar.

## Candidate Explicit CRUD Rerun Summary (2026-07-09 21:43 Asia/Taipei)

This rerun used the locally built candidate jar provided by the framework project and executed an explicit Oracle Testcontainers CRUD suite.

Candidate jar:

```text
/Users/herman_mbp2023/ClawProjects/skills/Spec Driven Auto Regression/target/spec-driven-auto-regression-0.2.5.jar
```

Command:

```bash
cd testcontainers-heavy-jdbc
PATH="/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:$PATH" \
DOCKER_CONFIG=/tmp/pirun-docker-config \
PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 \
PIRUN_ENABLE_ORACLE_TESTCONTAINER=1 \
PIRUN_FRAMEWORK_VERSION=0.2.5 \
PIRUN_FRAMEWORK_JAR="/Users/herman_mbp2023/ClawProjects/skills/Spec Driven Auto Regression/target/spec-driven-auto-regression-0.2.5.jar" \
PIRUN_ORACLE_TESTCONTAINER_IMAGE=gvenzl/oracle-free:23-slim-faststart \
PIRUN_REPO_ROOT=/Users/herman_mbp2023/Documents/test_framework_pirun \
MAVEN_OPTS="-Xmx1024m -XX:MaxMetaspaceSize=384m" \
./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#oracleContainerMustExecuteCrudWithFrameworkJdbcProvider test
```

Framework result:

```text
run_status: passed
suite_id: JDBC-CAPABILITY-v0.2
test_case_id: JDBC-CRUD-TC-001
passed_count: 1
provider_runtime_executed: true
provider_type: jdbc
provider_id: oracle-like-db
runtime_mode: native
dialect: oracle
findings:
  []
```

CRUD evidence:

| CRUD step | Framework operation | Result evidence |
| --- | --- | --- |
| Create order | `db_seed` / `fixtures/crud_insert_order.sql` | `seed_create_order.yaml`: `affected_rows: 1` |
| Read created order | `db_query` / `queries/crud_order_by_id_oracle.sql` | `query_read_created_order.yaml`: `row_count: 1`, `STATUS: CREATED` |
| Update order | `db_seed` / `fixtures/crud_update_order.sql` | `seed_update_order.yaml`: `affected_rows: 1` |
| Read updated order | `db_query` / `queries/crud_order_by_id_oracle.sql` | `query_read_updated_order.yaml`: `row_count: 1`, `STATUS: UPDATED` |
| Delete order | `db_cleanup` / `fixtures/crud_delete_order.sql` | `cleanup_delete_order.yaml`: `affected_rows: 1` |
| Read deleted order | `db_query` / `queries/crud_order_by_id_oracle.sql` | `query_read_deleted_order.yaml`: `row_count: 0` |
| Verify deleted row absent | `db_record_exists` with `expected_row_count: 0` | `query_deleted_order_record_absent.yaml`: `row_count: 0`, `status: passed` |

Evidence paths:

```text
.pirun/runs/PIRUN-TC-ORACLE-CRUD-1783604592863/jdbc_oracle_testcontainers/framework_stdout.txt
.pirun/runs/PIRUN-TC-ORACLE-CRUD-1783604592863/jdbc_oracle_testcontainers/test_case.yaml
artifacts/usage-kits/usage-kit-v0.2.5/usage-kit/target/provider-capability/jdbc/JDBC-CAPABILITY-v0.2/BATCH-JDBC-20260709134313939-1/RUN-JDBC-20260709134313939-1/result.json
artifacts/usage-kits/usage-kit-v0.2.5/usage-kit/target/provider-capability/jdbc/JDBC-CAPABILITY-v0.2/BATCH-JDBC-20260709134313939-1/RUN-JDBC-20260709134313939-1/provider-evidence/jdbc/
```

Candidate CRUD conclusion:

- Oracle JDBC provider CRUD was tested against a real Oracle Testcontainers runtime.
- The framework consumed the project-provided `env://JDBC_CONNECTION` through `PIRUN_FRAMEWORK_JAR`.
- The test covered create, read-after-create, update, read-after-update, delete, read-after-delete, and a framework verify check for deleted-row absence.
- DB2 CRUD was not run on this local 8 GiB-class Docker setup.

## Candidate Target Jar Rerun Summary (2026-07-09 21:26 Asia/Taipei)

This rerun used the locally built candidate jar provided by the framework project, not the GitHub release asset jar.

Candidate jar:

```text
/Users/herman_mbp2023/ClawProjects/skills/Spec Driven Auto Regression/target/spec-driven-auto-regression-0.2.5.jar
```

Candidate jar SHA-256:

```text
22f7cbb3511bb2bd3eb1d1f6097e89f4c134b1c0ed7c5f9257c60a7210efa5f8
```

The candidate jar differs from the downloaded v0.2.5 release asset jar, whose SHA-256 is:

```text
cc5bf11f14fab0f0ee019de405a391f8f6b9146dae478c5d3d59906522580a8b
```

Candidate command:

```bash
cd testcontainers-heavy-jdbc
PATH="/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:$PATH" \
DOCKER_CONFIG=/tmp/pirun-docker-config \
PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 \
PIRUN_ENABLE_ORACLE_TESTCONTAINER=1 \
PIRUN_FRAMEWORK_VERSION=0.2.5 \
PIRUN_FRAMEWORK_JAR="/Users/herman_mbp2023/ClawProjects/skills/Spec Driven Auto Regression/target/spec-driven-auto-regression-0.2.5.jar" \
PIRUN_ORACLE_TESTCONTAINER_IMAGE=gvenzl/oracle-free:23-slim-faststart \
PIRUN_REPO_ROOT=/Users/herman_mbp2023/Documents/test_framework_pirun \
MAVEN_OPTS="-Xmx1024m -XX:MaxMetaspaceSize=384m" \
./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#oracleContainerMustBeConsumedByFrameworkJdbcProvider test
```

Candidate result:

| Check | Result | Evidence |
| --- | --- | --- |
| Harness jar selection | PASS | `framework_invocation.json` contains the candidate target jar path and does not contain the release asset jar path. |
| Oracle Testcontainers provisioning | PASS | Oracle Free image `gvenzl/oracle-free:23-slim-faststart`; dialect probe passed. |
| Oracle framework JDBC provider consumption | PASS | Framework exited `0`; `run_status: passed`; `provider_runtime_executed: true`; `provider_id: oracle-like-db`. |
| Docker cleanup | PASS | No containers left after the run. |

Candidate Oracle evidence:

```text
.pirun/runs/PIRUN-TC-ORACLE-1783603594174/jdbc_oracle_testcontainers/framework_stdout.txt
.pirun/runs/PIRUN-TC-ORACLE-1783603594174/jdbc_oracle_testcontainers/environment_bindings/ci.yaml
.pirun/runs/PIRUN-TC-ORACLE-1783603594174/jdbc_oracle_testcontainers/framework_invocation.json
testcontainers-heavy-jdbc/target/surefire-reports/pirun.heavyjdbc.HeavyJdbcProviderTestcontainersIT.txt
```

Candidate Oracle framework stdout:

```text
run_status: passed
provider_runtime_executed: true
provider_type: jdbc
provider_id: oracle-like-db
runtime_mode: native
dialect: oracle
findings:
  []
```

Candidate conclusion:

- The target jar fixes Oracle JDBC `env://JDBC_CONNECTION` consumption for project-provisioned Testcontainers.
- DB2 was not rerun on this local 8 GiB-class Docker setup.
- This is candidate-build evidence, not published release-asset evidence.

## Release Asset Rerun Summary (2026-07-09 21:00 Asia/Taipei)

This rerun used the Java Testcontainers harness, the local Docker Desktop daemon, and the v0.2.5 release asset already stored under `artifacts/release-assets/release-assets-v0.2.5/`.

| Check | Result | Evidence |
| --- | --- | --- |
| Docker daemon | PASS | Docker Server `28.4.0`; `MemTotal=8218316800`; no containers left after the run. |
| Oracle Testcontainers provisioning | PASS | Oracle Free image `gvenzl/oracle-free:23-slim-faststart`; 3 GiB container memory; dialect probe passed; cleanup passed. |
| Oracle framework JDBC provider consumption | FAIL, framework issue | Harness materialized `env://JDBC_CONNECTION`, set `JDBC_CONNECTION` in the framework process env, and framework exited `1` with `SECRET_RESOLUTION_ERROR`. |
| DB2 Testcontainers provisioning | NOT RUN on this machine | Project gate skipped because DB2 license/privileged opt-ins were not set; Docker memory `8218316800` bytes is also below the 8 GiB DB2 gate. |

Release asset Oracle Testcontainers evidence:

```text
.pirun/runs/PIRUN-TC-ORACLE-1783602028780/jdbc_oracle_testcontainers/framework_stdout.txt
.pirun/runs/PIRUN-TC-ORACLE-1783602028780/jdbc_oracle_testcontainers/environment_bindings/ci.yaml
testcontainers-heavy-jdbc/target/surefire-reports/pirun.heavyjdbc.HeavyJdbcProviderTestcontainersIT.txt
```

Release asset Oracle framework stdout:

```text
run_status: failed
provider_runtime_executed: true
provider_type: jdbc
provider_id: oracle-like-db
runtime_mode: native
dialect: oracle
failure_code: SECRET_RESOLUTION_ERROR
failure_reason: JDBC secret_ref `env://JDBC_CONNECTION` cannot be resolved by local provider capability runtime.
```

Release asset DB2 gate report:

```text
.pirun/runs/PIRUN-V025-DB2-GATE-20260709/jdbc_db2_container/project_report.json
```

Release asset conclusion:

- Oracle proves the Testcontainers harness can provision a real database and reach the framework JDBC runtime.
- v0.2.5 still fails the framework acceptance condition because the JDBC provider runtime does not resolve project-provided `env://` connection refs.
- DB2 should be rerun on CI or a larger local Docker allocation after explicit DB2 license/privileged opt-in.

## Commands

Wrapper and compile gate:

```bash
cd testcontainers-heavy-jdbc
MAVEN_OPTS="-Xmx512m" ./mvnw -version
MAVEN_OPTS="-Xmx1024m" ./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT test
```

Oracle-only acceptance attempt:

```bash
cd testcontainers-heavy-jdbc
PATH="/usr/local/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH" \
PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 \
PIRUN_ENABLE_ORACLE_TESTCONTAINER=1 \
PIRUN_FRAMEWORK_VERSION=0.2.5 \
MAVEN_OPTS="-Xmx1024m" \
./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#oracleContainerMustBeConsumedByFrameworkJdbcProvider test
```

DB2-only acceptance attempt:

```bash
cd testcontainers-heavy-jdbc
PATH="/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:/opt/homebrew/bin:$PATH" \
PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 \
PIRUN_ENABLE_DB2_TESTCONTAINER=1 \
PIRUN_ACCEPT_DB2_LICENSE=1 \
PIRUN_ALLOW_PRIVILEGED_DB2=1 \
PIRUN_FRAMEWORK_VERSION=0.2.5 \
MAVEN_OPTS="-Xmx1024m" \
./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#db2ContainerMustBeConsumedByFrameworkJdbcProvider test
```

## Environment

- Docker Desktop daemon: available.
- Docker memory: 8,218,316,800 bytes.
- Running containers before DB2 attempt: none.
- Running containers after DB2 attempt: none.
- Oracle image used by Testcontainers: `gvenzl/oracle-free:23-slim-faststart`.
- DB2 image used by Testcontainers: `icr.io/db2_community/db2:11.5.8.0`.
- Oracle container memory limit in harness: 3 GiB, shm 1 GiB.
- DB2 container memory limit in harness: 6 GiB.
- Java/Maven heap guardrail: `MAVEN_OPTS="-Xmx1024m"` and forked framework JVM `-Xmx512m`.

## Historical Full Heavy-JDBC Result

This section records the prior full Oracle and DB2 attempts already captured in this report. Use the candidate and release asset rerun summaries above for the 2026-07-09 local-machine acceptance status.

Classification: `FRAMEWORK_ISSUE_SECRET_RESOLUTION`

What passed:

- Maven Wrapper works with Apache Maven 3.9.11.
- Maven Wrapper distribution is checksum-pinned.
- Java Testcontainers harness compiles.
- Harness output artifacts redact JDBC secrets before writing evidence.
- Opt-in gates prevent accidental heavy DB startup.
- Oracle Testcontainers provisioning reached framework invocation.
- DB2 Testcontainers provisioning reached framework invocation.
- Materialized suites used project-owned JDBC binding:
  - `runtime_mode: native`
  - `connection.secret_ref: env://JDBC_CONNECTION`
  - `allowed_provisioners: project_docker`
- Framework JDBC provider runtime was invoked for both Oracle and DB2.
- Docker cleanup left 0 running containers after the DB2 attempt.

Oracle framework stdout evidence:

```text
run_status: failed
provider_runtime_executed: true
provider_type: jdbc
provider_id: oracle-like-db
runtime_mode: native
dialect: oracle
failure_code: SECRET_RESOLUTION_ERROR
failure_reason: JDBC secret_ref `env://JDBC_CONNECTION` cannot be resolved by local provider capability runtime.
owner_action: Use a supported generated:// provider capability secret ref for local_jdbc or configure a secret resolver.
```

DB2 framework stdout evidence:

```text
run_status: failed
provider_runtime_executed: true
provider_type: jdbc
provider_id: db2-like-db
runtime_mode: native
dialect: db2
failure_code: SECRET_RESOLUTION_ERROR
failure_reason: JDBC secret_ref `env://JDBC_CONNECTION` cannot be resolved by local provider capability runtime.
owner_action: Use a supported generated:// provider capability secret ref for local_jdbc or configure a secret resolver.
```

Evidence paths:

```text
.pirun/runs/PIRUN-TC-ORACLE-1783593641329/jdbc_oracle_testcontainers/framework_stdout.txt
.pirun/runs/PIRUN-TC-DB2-1783595732804/jdbc_db2_testcontainers/framework_stdout.txt
testcontainers-heavy-jdbc/target/surefire-reports/pirun.heavyjdbc.HeavyJdbcProviderTestcontainersIT.txt
```

## Finding

The published v0.2.5 release asset cannot complete project-provisioned Oracle or DB2 JDBC provider acceptance because the framework JDBC provider runtime does not resolve `env://JDBC_CONNECTION`.

The project can provision Oracle and DB2, prove direct JDBC connectivity, create the `ORDERS` table, inject vendor JDBC drivers, and materialize framework-valid native JDBC suites. The published release asset still only accepts its local/generated JDBC secret path for provider capability execution.

The local candidate target jar passes the Oracle Testcontainers acceptance path for `env://JDBC_CONNECTION`. DB2 remains unproven on this local machine.

This is a framework issue, not a project provisioning issue.

## Framework Fix Required

For the published release asset, add JDBC provider secret resolution support for project-supplied environment secret refs:

```yaml
connection:
  secret_ref: env://JDBC_CONNECTION
```

Acceptance for the framework fix:

- `env://JDBC_CONNECTION` resolves at runtime.
- JDBC provider uses the resolved external connection string, not generated H2.
- Failure output redacts the connection value and password.
- Oracle Testcontainers run passes with `provider_runtime_executed: true`, `provider_id: oracle-like-db`, and `run_status: passed`.
- DB2 Testcontainers run passes with `provider_runtime_executed: true`, `provider_id: db2-like-db`, and `run_status: passed`.
- The framework does not own Docker/Testcontainers provisioning.

## Project Status

The project-side Testcontainers harness is ready to rerun against a published release after the framework supports JDBC `env://` secret refs.

For the 2026-07-09 candidate target jar rerun, Oracle reached the framework and passed. DB2 was intentionally not started on this 8 GiB-class local Docker setup.
