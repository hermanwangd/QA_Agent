import tempfile
import unittest
from pathlib import Path

from pirun.provisioners.heavy_jdbc import (
    BYTES_PER_GIB,
    HeavyJdbcLock,
    build_heavy_jdbc_run_command,
    dialect_probe_exec_command,
    evaluate_resource_gate,
    jdbc_connection_url,
    parse_docker_port,
)


class HeavyJdbcGateTests(unittest.TestCase):
    def test_oracle_requires_global_opt_in(self):
        result = evaluate_resource_gate(
            "oracle",
            env={},
            docker_memory_bytes=8 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "SKIPPED_POLICY_GATE")
        self.assertIn("PIRUN_ENABLE_HEAVY_DB_CONTAINERS", result.reasons)

    def test_oracle_passes_with_opt_in_and_resources(self):
        result = evaluate_resource_gate(
            "oracle",
            env={
                "PIRUN_ENABLE_HEAVY_DB_CONTAINERS": "1",
                "PIRUN_ORACLE_IMAGE": "gvenzl/oracle-free:23-slim-faststart",
            },
            docker_memory_bytes=8 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "PASS")

    def test_db2_requires_license_and_privileged_gates(self):
        result = evaluate_resource_gate(
            "db2",
            env={"PIRUN_ENABLE_HEAVY_DB_CONTAINERS": "1"},
            docker_memory_bytes=16 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "SKIPPED_POLICY_GATE")
        self.assertIn("PIRUN_ACCEPT_DB2_LICENSE", result.reasons)
        self.assertIn("PIRUN_ALLOW_PRIVILEGED_DB2", result.reasons)

    def test_db2_skips_when_docker_memory_is_too_low(self):
        result = evaluate_resource_gate(
            "db2",
            env={
                "PIRUN_ENABLE_HEAVY_DB_CONTAINERS": "1",
                "PIRUN_ACCEPT_DB2_LICENSE": "1",
                "PIRUN_ALLOW_PRIVILEGED_DB2": "1",
            },
            docker_memory_bytes=4 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "SKIPPED_RESOURCE_LIMIT")
        self.assertIn("docker_memory", result.reasons)

    def test_parse_docker_port_accepts_ipv4_output(self):
        self.assertEqual(parse_docker_port("127.0.0.1:51521\n"), 51521)

    def test_lock_prevents_parallel_heavy_db_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock_path = Path(tmp) / "heavy-jdbc-container.lock"
            first = HeavyJdbcLock(lock_path)
            first.acquire()
            second = HeavyJdbcLock(lock_path)
            with self.assertRaises(RuntimeError):
                second.acquire()
            first.release()
            self.assertFalse(lock_path.exists())

    def test_oracle_run_command_uses_faststart_image_shm_and_app_user(self):
        command = build_heavy_jdbc_run_command(
            "oracle",
            run_id="RUN-ORACLE",
            image="gvenzl/oracle-free:23-slim-faststart",
            password="Secret-12345",
        )
        joined = " ".join(command)

        self.assertIn("--memory 3g", joined)
        self.assertIn("--shm-size 1g", joined)
        self.assertIn("ORACLE_PASSWORD=Secret-12345", joined)
        self.assertIn("APP_USER=APP", joined)
        self.assertIn("APP_USER_PASSWORD=Secret-12345", joined)
        self.assertIn("gvenzl/oracle-free:23-slim-faststart", joined)
        self.assertNotIn("--privileged", command)

    def test_db2_run_command_requires_privileged_license_and_password(self):
        command = build_heavy_jdbc_run_command(
            "db2",
            run_id="RUN-DB2",
            image="icr.io/db2_community/db2",
            password="Secret-12345",
        )
        joined = " ".join(command)

        self.assertIn("--privileged", command)
        self.assertIn("--memory 6g", joined)
        self.assertIn("LICENSE=accept", joined)
        self.assertIn("DB2INSTANCE=db2inst1", joined)
        self.assertIn("DB2INST1_PASSWORD=Secret-12345", joined)
        self.assertIn("DBNAME=testdb", joined)
        self.assertIn("icr.io/db2_community/db2", joined)

    def test_jdbc_connection_url_uses_engine_specific_format(self):
        self.assertEqual(
            jdbc_connection_url("oracle", 51521, service_name="FREEPDB1"),
            "jdbc:oracle:thin:@//127.0.0.1:51521/FREEPDB1",
        )
        self.assertEqual(jdbc_connection_url("db2", 55000), "jdbc:db2://127.0.0.1:55000/testdb")

    def test_dialect_probe_commands_use_engine_specific_sql(self):
        oracle = " ".join(dialect_probe_exec_command("oracle", password="Secret-12345"))
        db2 = " ".join(dialect_probe_exec_command("db2", password="Secret-12345"))

        self.assertIn("select 1 from dual", oracle)
        self.assertIn("sqlplus", oracle)
        self.assertIn("select 1 from sysibm.sysdummy1", db2)
        self.assertIn("db2 connect to testdb", db2)


if __name__ == "__main__":
    unittest.main()
