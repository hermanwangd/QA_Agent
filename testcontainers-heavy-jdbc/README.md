# Testcontainers Heavy JDBC PI-run Harness

This project-owned harness verifies whether the released framework JDBC provider can consume real Oracle Free and DB2 Testcontainers. It is not part of default PI-run and must be run one database at a time.

The framework release jar does not bundle Oracle or DB2 JDBC drivers. This harness supplies driver dependencies from Maven and launches the release jar through Spring Boot `PropertiesLauncher` with `loader.path` so the forked framework process can load those drivers.

## Prerequisites

- Docker Desktop or another Docker-compatible runtime.
- Java 17+.
- Maven Wrapper is checked in as `./mvnw`; no global Maven install is required.
- Local machine must stay under the 8 GB RAM constraint. DB2 should run only on a CI or machine with enough Docker memory.

## Oracle

```bash
cd testcontainers-heavy-jdbc
PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 \
PIRUN_ENABLE_ORACLE_TESTCONTAINER=1 \
PIRUN_FRAMEWORK_VERSION=0.2.5 \
MAVEN_OPTS="-Xmx1024m" \
./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#oracleContainerMustBeConsumedByFrameworkJdbcProvider test
```

Optional image override:

```bash
PIRUN_ORACLE_TESTCONTAINER_IMAGE=gvenzl/oracle-free:23-slim-faststart
```

## DB2

```bash
cd testcontainers-heavy-jdbc
PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 \
PIRUN_ENABLE_DB2_TESTCONTAINER=1 \
PIRUN_ACCEPT_DB2_LICENSE=1 \
PIRUN_ALLOW_PRIVILEGED_DB2=1 \
PIRUN_FRAMEWORK_VERSION=0.2.5 \
MAVEN_OPTS="-Xmx1024m" \
./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#db2ContainerMustBeConsumedByFrameworkJdbcProvider test
```

Optional image override:

```bash
PIRUN_DB2_TESTCONTAINER_IMAGE=icr.io/db2_community/db2:11.5.8.0
```

## Pass Condition

The dialect probe must connect to the container, create `ORDERS`, and execute the engine-specific SQL probe. The framework run must exit zero and print `provider_runtime_executed: true` or `provider_runtime_invoked: true` with the expected JDBC provider id.

If project provisioning passes but framework output does not prove JDBC provider consumption, this is a failed JDBC-provider acceptance result, not a pass.
