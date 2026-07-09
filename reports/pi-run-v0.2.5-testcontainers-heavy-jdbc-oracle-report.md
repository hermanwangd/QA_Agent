# pi-run v0.2.5 Testcontainers Heavy JDBC Oracle Report

Date: 2026-07-09

## Scope

Validate whether a project-owned Oracle Free Testcontainers runtime can be used to test the released framework JDBC provider in `spec-driven-auto-regression-0.2.5.jar`.

This is not a DB2 result. DB2 was not run locally because the machine is constrained to 8 GB RAM.

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

## Environment

- Docker Desktop daemon: available.
- Docker memory: 8,218,316,800 bytes.
- Running containers before Oracle attempt: none.
- Oracle image used by Testcontainers: `gvenzl/oracle-free:slim-faststart`.
- Oracle container memory limit in harness: 3 GiB, shm 1 GiB.

## Result

Classification: `FRAMEWORK_ISSUE_SECRET_RESOLUTION`

What passed:

- Maven Wrapper works with Apache Maven 3.9.11.
- Java Testcontainers harness compiles.
- Opt-in gates prevent accidental heavy DB startup.
- Oracle Testcontainers provisioning reached framework invocation.
- Materialized suite used project-owned JDBC binding:
  - `runtime_mode: native`
  - `connection.secret_ref: env://PIRUN_JDBC_CONNECTION`
  - `allowed_provisioners: project_docker`
- Framework JDBC provider runtime was invoked.

Framework stdout evidence:

```text
run_status: failed
provider_runtime_executed: true
provider_type: jdbc
provider_id: oracle-like-db
runtime_mode: native
dialect: oracle
failure_code: SECRET_RESOLUTION_ERROR
failure_reason: JDBC secret_ref `env://PIRUN_JDBC_CONNECTION` cannot be resolved by local provider capability runtime.
owner_action: Use a supported generated:// provider capability secret ref for local_jdbc or configure a secret resolver.
```

Evidence path:

```text
.pirun/runs/PIRUN-TC-ORACLE-1783593641329/jdbc_oracle_testcontainers/framework_stdout.txt
artifacts/usage-kits/usage-kit-v0.2.5/usage-kit/target/provider-capability/jdbc/JDBC-CAPABILITY-v0.2/BATCH-JDBC-20260709104042023-1/RUN-JDBC-20260709104042023-1/result.json
```

## Finding

`v0.2.5` cannot complete project-provisioned Oracle JDBC provider acceptance because the framework JDBC provider runtime does not resolve `env://PIRUN_JDBC_CONNECTION`.

The project can provision Oracle and materialize a framework-valid native JDBC suite, but the released framework still only accepts its local/generated JDBC secret path for provider capability execution.

## Framework Fix Required

Add JDBC provider secret resolution support for project-supplied environment secret refs:

```yaml
connection:
  secret_ref: env://PIRUN_JDBC_CONNECTION
```

Acceptance for the framework fix:

- `env://PIRUN_JDBC_CONNECTION` resolves at runtime.
- JDBC provider uses the resolved connection string, not generated H2.
- Failure output redacts the connection value.
- Oracle Testcontainers run passes with `provider_runtime_executed: true`, `provider_id: oracle-like-db`, and `run_status: passed`.

## Project Status

The project-side Testcontainers harness is ready to rerun after the framework supports JDBC `env://` secret refs.
