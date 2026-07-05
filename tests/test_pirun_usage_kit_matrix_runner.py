import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pirun.inspect_usage_kit import inspect_usage_kit
from pirun.run_contract_baseline import framework_paths
from pirun.run_usage_kit_matrix import build_matrix_plan, run_matrix_plan, write_run_report


class UsageKitMatrixRunnerTests(unittest.TestCase):
    def setUp(self):
        self.paths = framework_paths("0.2.3")
        self.inspection = inspect_usage_kit(self.paths.usage_kit_root)

    def test_matrix_plan_keeps_runnable_suites_and_blocked_rows_separate(self):
        plan = build_matrix_plan(
            self.inspection,
            framework_jar=self.paths.jar,
            usage_kit_root=self.paths.usage_kit_root,
            command_set=("validate",),
        )

        runnable_suites = {entry["suite"] for entry in plan["runnable_suites"]}
        blocked = {(row["provider_type"], row["runtime_mode"], row["expected_status"]) for row in plan["blocked_rows"]}

        self.assertIn("samples/provider_capability/kafka/suite_manifest.yaml", runnable_suites)
        self.assertIn(("kafka", "native", "BLOCKED_FRAMEWORK_CONTRACT_ONLY"), blocked)
        self.assertIn(("ibm_mq", "ephemeral", "BLOCKED_FRAMEWORK_CONTRACT_ONLY"), blocked)
        self.assertIn(("shell_command", "native", "BLOCKED_USAGE_KIT_SAMPLE_GAP"), blocked)

    def test_runner_uses_low_memory_java_commands(self):
        plan = {
            "framework_jar": str(self.paths.jar),
            "usage_kit_root": str(self.paths.usage_kit_root),
            "runnable_suites": [
                {
                    "suite": "samples/golden_e2e/suite_manifest.yaml",
                    "commands": ["validate", "run --dry-run"],
                }
            ],
            "blocked_rows": [],
        }
        completed = Mock(returncode=0, stdout="run_status: passed\n", stderr="")

        with patch("pirun.run_usage_kit_matrix.subprocess.run", return_value=completed) as run:
            report = run_matrix_plan(plan, execute=True)

        self.assertEqual(report["summary"]["unexpected_failures"], 0)
        self.assertEqual(len(report["suite_results"]), 2)
        for call in run.call_args_list:
            command = call.args[0]
            self.assertEqual(command[0:3], ["java", "-Xmx512m", "-jar"])

    def test_runner_redacts_raw_secrets_from_suite_output(self):
        plan = {
            "framework_jar": str(self.paths.jar),
            "usage_kit_root": str(self.paths.usage_kit_root),
            "runnable_suites": [
                {
                    "suite": "samples/golden_e2e/suite_manifest.yaml",
                    "commands": ["validate"],
                }
            ],
            "blocked_rows": [],
        }
        completed = Mock(
            returncode=0,
            stdout="run_status: passed\npassword=raw-secret-value\n",
            stderr="Authorization: Bearer abc.def\n",
        )

        with patch("pirun.run_usage_kit_matrix.subprocess.run", return_value=completed):
            report = run_matrix_plan(plan, execute=True)

        self.assertNotIn("raw-secret-value", report["suite_results"][0]["stdout"])
        self.assertNotIn("abc.def", report["suite_results"][0]["stderr"])
        self.assertIn("[REDACTED]", report["suite_results"][0]["stdout"])

    def test_runner_adds_suite_profile_for_real_run(self):
        plan = {
            "framework_jar": str(self.paths.jar),
            "usage_kit_root": str(self.paths.usage_kit_root),
            "runnable_suites": [
                {
                    "suite": "samples/provider_capability/kafka/suite_manifest.yaml",
                    "commands": ["run"],
                },
                {
                    "suite": "samples/contract_baseline/suite_manifest.yaml",
                    "commands": ["run"],
                },
            ],
            "blocked_rows": [],
        }
        completed = Mock(returncode=0, stdout="run_status: passed\n", stderr="")

        with patch("pirun.run_usage_kit_matrix.subprocess.run", return_value=completed) as run:
            run_matrix_plan(plan, execute=True)

        first = run.call_args_list[0].args[0]
        second = run.call_args_list[1].args[0]
        self.assertIn("--profile", first)
        self.assertEqual(first[first.index("--profile") + 1], "local_kafka")
        self.assertIn("--profile", second)
        self.assertEqual(second[second.index("--profile") + 1], "ci")

    def test_run_report_writes_json_and_markdown(self):
        report = {
            "summary": {
                "planned_suite_count": 1,
                "executed_command_count": 1,
                "unexpected_failures": 0,
                "blocked_row_count": 1,
            },
            "suite_results": [
                {
                    "suite": "samples/golden_e2e/suite_manifest.yaml",
                    "command": "validate",
                    "status": "PASS",
                    "exit_code": 0,
                }
            ],
            "blocked_rows": [
                {
                    "provider_type": "kafka",
                    "runtime_mode": "native",
                    "expected_status": "BLOCKED_FRAMEWORK_CONTRACT_ONLY",
                    "reason": "contract-only",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_run_report(report, Path(tmp), version="0.2.3")
            payload = json.loads(outputs["json"].read_text())
            markdown = outputs["markdown"].read_text()

        self.assertEqual(payload["summary"]["unexpected_failures"], 0)
        self.assertIn("samples/golden_e2e/suite_manifest.yaml", markdown)
        self.assertIn("BLOCKED_FRAMEWORK_CONTRACT_ONLY", markdown)


if __name__ == "__main__":
    unittest.main()
