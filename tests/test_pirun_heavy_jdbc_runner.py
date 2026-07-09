import json
import tempfile
import unittest
from pathlib import Path

from pirun.docker_cli import CommandResult
from pirun.provisioners.heavy_jdbc import BYTES_PER_GIB, GateResult
from pirun.run_heavy_jdbc_container import (
    classify_result,
    exit_code_for_classification,
    wait_for_dialect_probe,
    write_run_report,
    write_skip_report,
)


class HeavyJdbcRunnerTests(unittest.TestCase):
    def test_skip_report_writes_resource_gate_and_project_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "jdbc_oracle_container"
            gate = GateResult(
                engine="oracle",
                status="SKIPPED_RESOURCE_LIMIT",
                reasons=["docker_memory"],
                docker_memory_bytes=2 * BYTES_PER_GIB,
                disk_free_bytes=80 * BYTES_PER_GIB,
                required_docker_memory_bytes=4 * BYTES_PER_GIB,
                required_disk_free_bytes=25 * BYTES_PER_GIB,
            )

            write_skip_report(
                run_root=run_root,
                run_id="RUN-SKIP",
                mode="jdbc-oracle-container",
                gate=gate,
            )

            self.assertTrue((run_root / "resource_gate.yaml").exists())
            self.assertTrue((run_root / "provisioning_evidence.yaml").exists())
            self.assertTrue((run_root / "framework_stdout.txt").exists())
            self.assertTrue((run_root / "framework_stderr.txt").exists())
            report = json.loads((run_root / "project_report.json").read_text())
            self.assertEqual(report["result_classification"], "SKIPPED_RESOURCE_LIMIT")
            self.assertFalse(report["framework_invoked"])

    def test_classify_result_requires_framework_consumption_for_full_pass(self):
        self.assertEqual(
            classify_result(
                project_provisioned=True,
                dialect_probe_passed=True,
                framework_invoked=True,
                framework_exit_code=0,
                framework_consumed_external_jdbc=False,
                cleanup_passed=True,
            ),
            "PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN",
        )
        self.assertEqual(
            classify_result(
                project_provisioned=True,
                dialect_probe_passed=True,
                framework_invoked=True,
                framework_exit_code=0,
                framework_consumed_external_jdbc=True,
                cleanup_passed=True,
            ),
            "PASS",
        )

    def test_exit_code_marks_unproven_framework_consumption_as_failure(self):
        self.assertEqual(exit_code_for_classification("PASS"), 0)
        self.assertEqual(exit_code_for_classification("SKIPPED_POLICY_GATE"), 0)
        self.assertEqual(
            exit_code_for_classification("PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN"),
            1,
        )

    def test_wait_for_dialect_probe_retries_until_sql_succeeds(self):
        calls = []

        def fake_run(cmd, timeout=60):
            calls.append((cmd, timeout))
            if len(calls) == 1:
                return CommandResult(1, "", "not ready")
            return CommandResult(0, "1\n", "")

        result = wait_for_dialect_probe(
            engine="oracle",
            container_id="oracle-container",
            password="Secret-12345",
            timeout_seconds=3,
            interval_seconds=0,
            run_command_func=fake_run,
            sleep_func=lambda _: None,
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(len(calls), 2)
        self.assertIn("oracle-container", calls[0][0])

    def test_write_run_report_redacts_framework_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "jdbc_db2_container"
            gate = GateResult(
                engine="db2",
                status="PASS",
                reasons=[],
                docker_memory_bytes=16 * BYTES_PER_GIB,
                disk_free_bytes=80 * BYTES_PER_GIB,
                required_docker_memory_bytes=8 * BYTES_PER_GIB,
                required_disk_free_bytes=40 * BYTES_PER_GIB,
            )

            write_run_report(
                run_root=run_root,
                run_id="RUN-DB2",
                mode="jdbc-db2-container",
                db_engine="db2",
                image="icr.io/db2_community/db2",
                container_id="db2-container",
                container_memory="6g",
                shm_size=None,
                startup_timeout=900,
                startup_duration_seconds=12.5,
                host_port=55000,
                dialect_probe={"status": "passed", "attempts": 1, "stdout": "1\n", "stderr": ""},
                framework_invoked=True,
                framework_exit_code=0,
                framework_stdout="run_status: passed\npassword=raw-secret-value\n",
                framework_stderr="Authorization: Bearer abc.def\n",
                framework_consumed_external_jdbc=False,
                cleanup_status="passed",
                result_classification="PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN",
                gate=gate,
            )

            report = json.loads((run_root / "project_report.json").read_text())
            stdout = (run_root / "framework_stdout.txt").read_text()
            stderr = (run_root / "framework_stderr.txt").read_text()

        self.assertEqual(report["result_classification"], "PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN")
        self.assertIn("[REDACTED]", stdout)
        self.assertIn("[REDACTED]", stderr)


if __name__ == "__main__":
    unittest.main()
