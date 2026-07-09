import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = REPO_ROOT / "testcontainers-heavy-jdbc"
POM_PATH = HARNESS_ROOT / "pom.xml"
IT_PATH = HARNESS_ROOT / "src" / "test" / "java" / "pirun" / "heavyjdbc" / "HeavyJdbcProviderTestcontainersIT.java"
CLI_PATH = HARNESS_ROOT / "src" / "test" / "java" / "pirun" / "heavyjdbc" / "FrameworkCli.java"
REDACTOR_PATH = HARNESS_ROOT / "src" / "test" / "java" / "pirun" / "heavyjdbc" / "Redactor.java"
MATERIALIZER_PATH = HARNESS_ROOT / "src" / "test" / "java" / "pirun" / "heavyjdbc" / "SuiteMaterializer.java"
README_PATH = HARNESS_ROOT / "README.md"
MVNW_PATH = HARNESS_ROOT / "mvnw"
MVNW_CMD_PATH = HARNESS_ROOT / "mvnw.cmd"
WRAPPER_PROPERTIES_PATH = HARNESS_ROOT / ".mvn" / "wrapper" / "maven-wrapper.properties"


def _pom_dependencies() -> set[tuple[str, str]]:
    root = ET.parse(POM_PATH).getroot()
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    deps = set()
    for dep in root.findall(".//m:dependency", ns):
        group_id = dep.findtext("m:groupId", default="", namespaces=ns)
        artifact_id = dep.findtext("m:artifactId", default="", namespaces=ns)
        deps.add((group_id, artifact_id))
    return deps


class TestcontainersHeavyJdbcHarnessTests(unittest.TestCase):
    def test_maven_harness_declares_testcontainers_modules_and_vendor_drivers(self):
        self.assertTrue(POM_PATH.exists(), "testcontainers-heavy-jdbc/pom.xml must exist")

        deps = _pom_dependencies()

        self.assertIn(("org.testcontainers", "testcontainers-oracle-free"), deps)
        self.assertIn(("org.testcontainers", "testcontainers-db2"), deps)
        self.assertIn(("org.testcontainers", "testcontainers-junit-jupiter"), deps)
        self.assertIn(("com.oracle.database.jdbc", "ojdbc11"), deps)
        self.assertIn(("com.ibm.db2", "jcc"), deps)

    def test_maven_wrapper_is_project_owned(self):
        self.assertTrue(MVNW_PATH.exists(), "testcontainers-heavy-jdbc/mvnw must exist")
        self.assertTrue(MVNW_CMD_PATH.exists(), "testcontainers-heavy-jdbc/mvnw.cmd must exist")
        self.assertTrue(WRAPPER_PROPERTIES_PATH.exists(), "maven-wrapper.properties must exist")
        self.assertTrue(MVNW_PATH.stat().st_mode & 0o111, "mvnw must be executable")

        properties = WRAPPER_PROPERTIES_PATH.read_text(encoding="utf-8")
        self.assertIn("distributionUrl=", properties)
        self.assertRegex(properties, re.compile(r"^distributionSha256Sum=[0-9a-f]{64}$", re.MULTILINE))
        self.assertIn("apache-maven", properties)
        self.assertNotIn("maven-wrapper.jar", properties)

    def test_heavy_it_uses_opt_in_gates_before_starting_containers(self):
        text = IT_PATH.read_text(encoding="utf-8")

        self.assertIn("@Testcontainers", text)
        self.assertIn("OracleContainer", text)
        self.assertIn("Db2Container", text)
        self.assertIn(".acceptLicense()", text)
        self.assertIn("PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC", text)
        self.assertIn("PIRUN_ENABLE_ORACLE_TESTCONTAINER", text)
        self.assertIn("PIRUN_ENABLE_DB2_TESTCONTAINER", text)
        self.assertIn("PIRUN_ACCEPT_DB2_LICENSE", text)
        self.assertIn("PIRUN_ALLOW_PRIVILEGED_DB2", text)
        self.assertIn("withMemory", text)
        self.assertIn("withShmSize", text)
        self.assertIn("3L * GIB", text)
        self.assertIn("6L * GIB", text)
        self.assertNotIn('withDatabaseName("freepdb1")', text)
        self.assertRegex(text, re.compile(r"assumeHeavyEnabled\(.+oracle", re.DOTALL))
        self.assertRegex(text, re.compile(r"assumeHeavyEnabled\(.+db2", re.DOTALL))

    def test_framework_invocation_injects_drivers_and_requires_jdbc_provider_consumption(self):
        cli_text = CLI_PATH.read_text(encoding="utf-8")
        it_text = IT_PATH.read_text(encoding="utf-8")

        self.assertIn("PropertiesLauncher", cli_text)
        self.assertIn("loader.path", cli_text)
        self.assertIn("loader.main", cli_text)
        self.assertIn('env.put("JDBC_CONNECTION", jdbcConnection)', cli_text)
        self.assertNotIn("PIRUN_JDBC_CONNECTION", cli_text)
        self.assertIn("PIRUN_JDBC_USERNAME", cli_text)
        self.assertIn("PIRUN_JDBC_PASSWORD", cli_text)
        self.assertIn("Redactor.redact", cli_text)
        self.assertIn("provider_runtime_executed: true", it_text)
        self.assertIn("provider_runtime_invoked: true", it_text)
        self.assertIn("provider_ids:", it_text)
        self.assertIn("fail(", it_text)

    def test_framework_invocation_can_use_candidate_jar_override(self):
        cli_text = CLI_PATH.read_text(encoding="utf-8")

        self.assertIn("PIRUN_FRAMEWORK_JAR", cli_text)
        self.assertIn("candidate jar", cli_text)

    def test_framework_output_artifacts_are_redacted(self):
        self.assertTrue(REDACTOR_PATH.exists(), "Redactor.java must exist")
        cli_text = CLI_PATH.read_text(encoding="utf-8")

        self.assertIn("List.of(jdbcConnection, password)", cli_text)
        self.assertIn("new Result(process.exitValue(), stdout, stderr, command)", cli_text)
        self.assertNotIn("new Result(process.exitValue(), rawStdout, rawStderr, command)", cli_text)

    def test_materializer_uses_release_usage_kit_samples_and_external_binding(self):
        text = MATERIALIZER_PATH.read_text(encoding="utf-8")

        self.assertIn("artifacts/usage-kits/usage-kit-v", text)
        self.assertIn("materialize_heavy_jdbc_container", text)
        self.assertIn("env://JDBC_CONNECTION", text)
        self.assertIn("provider_id", text)
        self.assertIn("dialect", text)

    def test_heavy_it_has_oracle_crud_acceptance_path(self):
        it_text = IT_PATH.read_text(encoding="utf-8")
        materializer_text = MATERIALIZER_PATH.read_text(encoding="utf-8")

        self.assertIn("oracleContainerMustExecuteCrudWithFrameworkJdbcProvider", it_text)
        self.assertIn("materializeCrud", it_text)
        self.assertIn("JDBC-CRUD-TC-001", it_text)
        self.assertIn("materialize_heavy_jdbc_crud_container", materializer_text)

    def test_process_timeout_is_handled_before_stream_reads(self):
        for path in [CLI_PATH, MATERIALIZER_PATH]:
            text = path.read_text(encoding="utf-8")
            timeout_check = text.find("if (!finished)")
            first_stream_read = text.find("readAllBytes")
            self.assertNotEqual(timeout_check, -1, f"{path} must check process timeout")
            self.assertNotEqual(first_stream_read, -1, f"{path} must capture process output")
            self.assertLess(timeout_check, first_stream_read, f"{path} must kill timed-out process before reading streams")

    def test_readme_documents_resource_license_and_maven_commands(self):
        text = README_PATH.read_text(encoding="utf-8")

        self.assertIn("not part of default PI-run", text)
        self.assertIn("PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1", text)
        self.assertIn("PIRUN_ENABLE_ORACLE_TESTCONTAINER=1", text)
        self.assertIn("PIRUN_ENABLE_DB2_TESTCONTAINER=1", text)
        self.assertIn("PIRUN_ACCEPT_DB2_LICENSE=1", text)
        self.assertIn("PIRUN_ALLOW_PRIVILEGED_DB2=1", text)
        self.assertIn("MAVEN_OPTS=\"-Xmx1024m\"", text)
        self.assertIn("./mvnw", text)
        self.assertNotIn(" mvn ", text)


if __name__ == "__main__":
    unittest.main()
