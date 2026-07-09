# Proposal: Isolated Oracle and DB2 JDBC Container PI-run

Date: 2026-07-09

## Scope

Add two opt-in, isolated heavy JDBC database runs for the PI-run project:

- `jdbc-oracle-container`
- `jdbc-db2-container`

These modes validate real Oracle-compatible and DB2 JDBC behavior one database at a time. They are not part of the default acceptance matrix, not part of `full-contract-baseline`, and not owned by the framework jar.

## Runtime Boundary

Use project-side Docker provisioning first, not framework-side provisioning.

Implementation target:

```text
pirun/run_heavy_jdbc_container.py --db oracle
pirun/run_heavy_jdbc_container.py --db db2
```

The runner should use the existing Python PI-run harness style and Docker CLI wrappers. Do not add Java Testcontainers, Python `testcontainers`, or docker-java to the framework jar for this slice.

If strict Testcontainers-library semantics are later required, create a separate CI-only Java harness using Testcontainers modules and keep it outside the released framework runtime.

## Non-Goals

- Do not run Oracle and DB2 together.
- Do not run DB2 on the 8G local machine by default.
- Do not add Oracle/DB2 to normal PR checks.
- Do not embed Testcontainers provisioning into `spec-driven-auto-regression-*.jar`.
- Do not call a run fully passed unless the framework consumes the external JDBC binding and produces expected JDBC evidence.

## Resource Gates

All heavy DB modes require explicit opt-in:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1
```

Minimum local prechecks:

| Mode | Docker memory gate | Disk free gate | Default locality |
|---|---:|---:|---|
| `jdbc-oracle-container` | >= 4 GB Docker memory | >= 25 GB | local/manual opt-in allowed |
| `jdbc-db2-container` | >= 8 GB Docker memory | >= 40 GB | CI-only by default |

If gates fail, return `SKIPPED_RESOURCE_LIMIT`, not failed.

Oracle/DB2 must never run in parallel. The runner should use a local lock file:

```text
.pirun/locks/heavy-jdbc-container.lock
```

## Oracle Mode

Recommended image family:

```text
gvenzl/oracle-free:23-slim-faststart
```

Fallback:

```text
gvenzl/oracle-xe:21-slim-faststart
```

Container config:

```text
memory: 3g
shm_size: 1g
startup_timeout: 10m
port: dynamic host port -> 1521
```

Required gates:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1
PIRUN_ORACLE_IMAGE=gvenzl/oracle-free:23-slim-faststart
```

Acceptance SQL:

```sql
select 1 from dual
```

Then run:

- create test user/schema or use configured app user;
- create table;
- insert one row;
- query inserted row;
- cleanup table/schema artifacts.

Expected status model:

| Stage | Expected |
|---|---|
| Project provisioning | `PASS` when container starts and JDBC connection works |
| Dialect proof | `PASS` only if `select 1 from dual` succeeds |
| Framework consumption | `PASS` only if released framework consumes `env://PIRUN_JDBC_CONNECTION` or equivalent external binding |
| Cleanup | `PASS` only if container is removed and no labeled heavy DB containers remain |

If framework external JDBC binding is not consumed, report:

```text
PROJECT_PROVISIONING_PASS
FRAMEWORK_CONSUMPTION_NOT_PROVEN
```

## DB2 Mode

Recommended image:

```text
icr.io/db2_community/db2
```

Container config:

```text
memory: 6g minimum, 8g preferred
startup_timeout: 15m
port: dynamic host port -> 50000
privileged: true
```

Required gates:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1
PIRUN_ACCEPT_DB2_LICENSE=1
PIRUN_ALLOW_PRIVILEGED_DB2=1
```

Required DB2 env:

```text
LICENSE=accept
DB2INSTANCE=db2inst1
DB2INST1_PASSWORD=<generated-secret>
DBNAME=testdb
BLU=false
ENABLE_ORACLE_COMPATIBILITY=false
TO_CREATE_SAMPLEDB=false
REPODB=false
```

Acceptance SQL:

```sql
select 1 from sysibm.sysdummy1
```

Then run:

- create schema/table;
- insert one row;
- query inserted row;
- cleanup table/schema artifacts.

Expected status model:

| Stage | Expected |
|---|---|
| Project provisioning | `PASS` when privileged DB2 container starts and JDBC connection works |
| Dialect proof | `PASS` only if `select 1 from sysibm.sysdummy1` succeeds |
| Framework consumption | `PASS` only if released framework consumes `env://PIRUN_JDBC_CONNECTION` or equivalent external binding |
| Cleanup | `PASS` only if container is removed and no labeled DB2 containers remain |

If DB2 gates are absent, return:

```text
SKIPPED_POLICY_GATE
```

If memory/disk gates fail, return:

```text
SKIPPED_RESOURCE_LIMIT
```

## Materialized Framework Artifacts

The project runner should materialize a suite workspace under:

```text
.pirun/runs/<run_id>/jdbc_<db>_container/
```

The generated suite must replace embedded H2/generated refs with project-owned external binding:

```yaml
provider_bindings:
  - provider_id: oracle-like-db
    runtime_mode: external
    binding_values:
      connection:
        secret_ref: env://PIRUN_JDBC_CONNECTION
      dialect: oracle
```

For DB2:

```yaml
provider_bindings:
  - provider_id: db2-like-db
    runtime_mode: external
    binding_values:
      connection:
        secret_ref: env://PIRUN_JDBC_CONNECTION
      dialect: db2
```

The runner must redact the actual connection URL in all reports.

## Report Output

Each run must write:

```text
project_report.json
provisioning_evidence.yaml
framework_stdout.txt
framework_stderr.txt
dialect_probe.yaml
cleanup_evidence.yaml
resource_gate.yaml
```

Required result fields:

```yaml
mode: jdbc-oracle-container | jdbc-db2-container
db_engine: oracle | db2
image:
container_id:
container_memory:
shm_size:
startup_timeout:
startup_duration_seconds:
readiness_status:
dialect_probe_status:
framework_invoked:
framework_consumed_external_jdbc:
cleanup_status:
result_classification:
```

## Acceptance Criteria

Oracle acceptance:

- Resource gates pass.
- Oracle container starts within timeout.
- JDBC connection succeeds.
- `select 1 from dual` succeeds.
- Seed/query/cleanup succeeds.
- Framework is invoked with external JDBC binding.
- Framework consumption is either proven or explicitly classified as `FRAMEWORK_CONSUMPTION_NOT_PROVEN`.
- Cleanup leaves zero labeled Oracle containers.

DB2 acceptance:

- DB2 license and privileged gates are explicitly set.
- Resource gates pass.
- DB2 container starts within timeout.
- JDBC connection succeeds.
- `select 1 from sysibm.sysdummy1` succeeds.
- Seed/query/cleanup succeeds.
- Framework is invoked with external JDBC binding.
- Framework consumption is either proven or explicitly classified as `FRAMEWORK_CONSUMPTION_NOT_PROVEN`.
- Cleanup leaves zero labeled DB2 containers.

## Recommended Rollout

1. Implement Oracle-only project-side Docker runner.
2. Run Oracle manually on a machine with >= 16 GB host RAM.
3. Add DB2 runner but mark it CI-only unless explicitly overridden.
4. Run DB2 only on dedicated runner with >= 16 GB host RAM and preferably 24 GB+.
5. Compare Oracle/DB2 evidence shape.
6. Decide whether nightly scheduling is useful. Do not add either mode to default PR.

## References

- Oracle XE requirements: `1 GB` minimum RAM, `2 GB` recommended RAM, `10 GB` disk minimum.
  https://docs.oracle.com/en/database/oracle/oracle-database/21/xeinl/requirements.html
- Oracle AI Database Free resource limits include up to `2 GB` database RAM, `2` CPU threads, and `12 GB` user data.
  https://www.oracle.com/database/free/
- Oracle container shared memory failures have been observed when `/dev/shm` is below `1 GB`.
  https://github.com/oracle/docker-images/issues/458
- IBM Db2 Community Edition Docker docs state preset/usage limits of `16GB` memory and `4` cores and show `--privileged=true`.
  https://www.ibm.com/docs/en/db2/11.5.x?topic=system-macos
  https://www.ibm.com/docs/en/db2/11.5.x?topic=system-linux
