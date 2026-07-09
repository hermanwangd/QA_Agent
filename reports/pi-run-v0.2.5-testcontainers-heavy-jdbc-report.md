# pi-run v0.2.5 Testcontainers Heavy JDBC Report

Date: 2026-07-09 Asia/Taipei

## Scope

Validate whether project-owned Oracle Free and DB2 Testcontainers runtimes can be used to test the released framework JDBC provider in `spec-driven-auto-regression-0.2.5.jar`.

The test framework release jar does not provision Oracle or DB2. This PI-run project provisions the database container, injects vendor JDBC drivers through the Maven harness, materializes a native JDBC suite, and invokes the released framework jar.

## Current Rerun Summary (2026-07-09 21:00 Asia/Taipei)

This rerun used the Java Testcontainers harness, the local Docker Desktop daemon, and the v0.2.5 release asset already stored under `artifacts/release-assets/release-assets-v0.2.5/`.

| Check | Result | Evidence |
| --- | --- | --- |
| Docker daemon | PASS | Docker Server `28.4.0`; `MemTotal=8218316800`; no containers left after the run. |
| Oracle Testcontainers provisioning | PASS | Oracle Free image `gvenzl/oracle-free:23-slim-faststart`; 3 GiB container memory; dialect probe passed; cleanup passed. |
| Oracle framework JDBC provider consumption | FAIL, framework issue | Harness materialized `env://JDBC_CONNECTION`, set `JDBC_CONNECTION` in the framework process env, and framework exited `1` with `SECRET_RESOLUTION_ERROR`. |
| DB2 Testcontainers provisioning | NOT RUN on this machine | Project gate skipped because DB2 license/privileged opt-ins were not set; Docker memory `8218316800` bytes is also below the 8 GiB DB2 gate. |

Current Oracle Testcontainers evidence:

```text
.pirun/runs/PIRUN-TC-ORACLE-1783602028780/jdbc_oracle_testcontainers/framework_stdout.txt
.pirun/runs/PIRUN-TC-ORACLE-1783602028780/jdbc_oracle_testcontainers/environment_bindings/ci.yaml
testcontainers-heavy-jdbc/target/surefire-reports/pirun.heavyjdbc.HeavyJdbcProviderTestcontainersIT.txt
```

Current Oracle framework stdout:

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

Current DB2 gate report:

```text
.pirun/runs/PIRUN-V025-DB2-GATE-20260709/jdbc_db2_container/project_report.json
```

Current conclusion:

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
- Oracle image used by Testcontainers: `gvenzl/oracle-free:slim-faststart`.
- DB2 image used by Testcontainers: `icr.io/db2_community/db2:11.5.8.0`.
- Oracle container memory limit in harness: 3 GiB, shm 1 GiB.
- DB2 container memory limit in harness: 6 GiB.
- Java/Maven heap guardrail: `MAVEN_OPTS="-Xmx1024m"` and forked framework JVM `-Xmx512m`.

## Historical Full Heavy-JDBC Result

This section records the prior full Oracle and DB2 attempts already captured in this report. Use the current rerun summary above for the 2026-07-09 local-machine acceptance status.

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

`v0.2.5` cannot complete project-provisioned Oracle or DB2 JDBC provider acceptance because the framework JDBC provider runtime does not resolve `env://JDBC_CONNECTION`.

The project can provision Oracle and DB2, prove direct JDBC connectivity, create the `ORDERS` table, inject vendor JDBC drivers, and materialize framework-valid native JDBC suites. The released framework still only accepts its local/generated JDBC secret path for provider capability execution.

This is a framework issue, not a project provisioning issue.

## Framework Fix Required

Add JDBC provider secret resolution support for project-supplied environment secret refs:

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

The project-side Testcontainers harness is ready to rerun after the framework supports JDBC `env://` secret refs.

For the current 2026-07-09 rerun, Oracle reached the framework and failed on `SECRET_RESOLUTION_ERROR`; DB2 was intentionally not started on this 8 GiB-class local Docker setup.
