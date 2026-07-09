package pirun.heavyjdbc;

import static org.junit.jupiter.api.Assertions.fail;

import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import java.util.Locale;
import java.util.Map;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;
import org.testcontainers.db2.Db2Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.oracle.OracleContainer;

@Testcontainers
class HeavyJdbcProviderTestcontainersIT {
    private static final String DEFAULT_FRAMEWORK_VERSION = "0.2.5";
    private static final String PROFILE = "ci";
    private static final String ORACLE_PROVIDER_ID = "oracle-like-db";
    private static final String DB2_PROVIDER_ID = "db2-like-db";

    @Test
    void oracleContainerMustBeConsumedByFrameworkJdbcProvider() throws Exception {
        assumeHeavyEnabled("oracle");
        String password = envOrDefault("PIRUN_ORACLE_TEST_PASSWORD", "PirunOracle12345");
        // Manual lifecycle keeps opt-in assumptions ahead of heavy container startup.
        // Source: https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/
        try (OracleContainer oracle = new OracleContainer(oracleImage())
            .withUsername("APP")
            .withPassword(password)
            .withDatabaseName("freepdb1")
            .withStartupTimeout(Duration.ofMinutes(10))) {
            oracle.start();
            assertSql(oracle.getJdbcUrl(), oracle.getUsername(), oracle.getPassword(), "select 1 from dual");
            ensureOrdersTable(oracle.getJdbcUrl(), oracle.getUsername(), oracle.getPassword(), "oracle");

            Path repoRoot = repoRoot();
            String frameworkVersion = frameworkVersion();
            Path runDir = SuiteMaterializer.materialize(
                repoRoot,
                "PIRUN-TC-ORACLE-" + System.currentTimeMillis(),
                frameworkVersion,
                ORACLE_PROVIDER_ID,
                "oracle",
                PROFILE
            );

            FrameworkCli.Result result = FrameworkCli.run(
                repoRoot,
                runDir,
                frameworkVersion,
                PROFILE,
                frameworkJdbcConnection("oracle", oracle.getJdbcUrl(), oracle.getUsername(), oracle.getPassword()),
                oracle.getUsername(),
                oracle.getPassword()
            );
            result.writeTo(runDir);
            assertFrameworkConsumed(result, ORACLE_PROVIDER_ID);
        }
    }

    @Test
    void db2ContainerMustBeConsumedByFrameworkJdbcProvider() throws Exception {
        assumeHeavyEnabled("db2");
        String password = envOrDefault("PIRUN_DB2_TEST_PASSWORD", "PirunDb212345");
        // DB2 module requires explicit license acceptance before use.
        // Source: https://java.testcontainers.org/modules/databases/db2/
        try (Db2Container db2 = new Db2Container(db2Image())
            .acceptLicense()
            .withUsername("db2inst1")
            .withPassword(password)
            .withDatabaseName("testdb")
            .withStartupTimeout(Duration.ofMinutes(15))) {
            db2.start();
            assertSql(db2.getJdbcUrl(), db2.getUsername(), db2.getPassword(), "select 1 from sysibm.sysdummy1");
            ensureOrdersTable(db2.getJdbcUrl(), db2.getUsername(), db2.getPassword(), "db2");

            Path repoRoot = repoRoot();
            String frameworkVersion = frameworkVersion();
            Path runDir = SuiteMaterializer.materialize(
                repoRoot,
                "PIRUN-TC-DB2-" + System.currentTimeMillis(),
                frameworkVersion,
                DB2_PROVIDER_ID,
                "db2",
                PROFILE
            );

            FrameworkCli.Result result = FrameworkCli.run(
                repoRoot,
                runDir,
                frameworkVersion,
                PROFILE,
                frameworkJdbcConnection("db2", db2.getJdbcUrl(), db2.getUsername(), db2.getPassword()),
                db2.getUsername(),
                db2.getPassword()
            );
            result.writeTo(runDir);
            assertFrameworkConsumed(result, DB2_PROVIDER_ID);
        }
    }

    private static void assumeHeavyEnabled(String engine) {
        Map<String, String> env = System.getenv();
        Assumptions.assumeTrue("1".equals(env.get("PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC")),
            "PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 is required");
        if ("oracle".equals(engine)) {
            Assumptions.assumeTrue("1".equals(env.get("PIRUN_ENABLE_ORACLE_TESTCONTAINER")),
                "PIRUN_ENABLE_ORACLE_TESTCONTAINER=1 is required");
        }
        if ("db2".equals(engine)) {
            Assumptions.assumeTrue("1".equals(env.get("PIRUN_ENABLE_DB2_TESTCONTAINER")),
                "PIRUN_ENABLE_DB2_TESTCONTAINER=1 is required");
            Assumptions.assumeTrue("1".equals(env.get("PIRUN_ACCEPT_DB2_LICENSE")),
                "PIRUN_ACCEPT_DB2_LICENSE=1 is required");
            Assumptions.assumeTrue("1".equals(env.get("PIRUN_ALLOW_PRIVILEGED_DB2")),
                "PIRUN_ALLOW_PRIVILEGED_DB2=1 is required");
        }
    }

    private static void assertFrameworkConsumed(FrameworkCli.Result result, String providerId) {
        if (result.exitCode() != 0) {
            fail("framework JDBC provider run failed with exit " + result.exitCode() + "\n" + result.stderr());
        }
        boolean runtimeExecuted = result.stdout().contains("provider_runtime_executed: true")
            || result.stdout().contains("provider_runtime_invoked: true");
        boolean providerSeen = result.stdout().contains("provider_id: " + providerId)
            || result.stdout().contains("provider_ids: " + providerId)
            || result.stdout().contains(providerId);
        if (!runtimeExecuted || !providerSeen) {
            fail("framework JDBC provider consumption not proven for " + providerId + "\n" + result.stdout());
        }
    }

    private static void assertSql(String jdbcUrl, String username, String password, String sql) throws SQLException {
        try (Connection connection = DriverManager.getConnection(jdbcUrl, username, password);
             Statement statement = connection.createStatement()) {
            statement.execute(sql);
        }
    }

    private static void ensureOrdersTable(String jdbcUrl, String username, String password, String engine)
        throws SQLException {
        String sql = "oracle".equals(engine)
            ? "create table ORDERS (ORDER_ID varchar2(64) primary key, STATUS varchar2(32))"
            : "create table ORDERS (ORDER_ID varchar(64) not null primary key, STATUS varchar(32))";
        try (Connection connection = DriverManager.getConnection(jdbcUrl, username, password);
             Statement statement = connection.createStatement()) {
            statement.execute(sql);
        } catch (SQLException exc) {
            if (!isTableExists(engine, exc)) {
                throw exc;
            }
        }
    }

    private static boolean isTableExists(String engine, SQLException exc) {
        String state = String.valueOf(exc.getSQLState()).toUpperCase(Locale.ROOT);
        if ("oracle".equals(engine)) {
            return exc.getErrorCode() == 955;
        }
        return "42710".equals(state) || exc.getErrorCode() == -601;
    }

    private static String frameworkJdbcConnection(String engine, String jdbcUrl, String username, String password) {
        if ("oracle".equals(engine)) {
            return jdbcUrl.replace("jdbc:oracle:thin:@", "jdbc:oracle:thin:" + username + "/" + password + "@");
        }
        String separator = jdbcUrl.endsWith(";") ? "" : ":";
        return jdbcUrl + separator + "user=" + username + ";password=" + password + ";";
    }

    private static Path repoRoot() {
        String configured = System.getenv("PIRUN_REPO_ROOT");
        if (configured != null && !configured.isBlank()) {
            return Path.of(configured).toAbsolutePath().normalize();
        }
        return Path.of("..").toAbsolutePath().normalize();
    }

    private static String frameworkVersion() {
        return envOrDefault("PIRUN_FRAMEWORK_VERSION", DEFAULT_FRAMEWORK_VERSION);
    }

    private static String oracleImage() {
        return envOrDefault("PIRUN_ORACLE_TESTCONTAINER_IMAGE", "gvenzl/oracle-free:slim-faststart");
    }

    private static String db2Image() {
        return envOrDefault("PIRUN_DB2_TESTCONTAINER_IMAGE", "icr.io/db2_community/db2:11.5.8.0");
    }

    private static String envOrDefault(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? fallback : value;
    }
}
