import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pirun.provisioners.nats import NatsProvisionResult
from pirun.run_contract_baseline import (
    MODE_SEQUENCE,
    ProvisioningError,
    framework_paths,
    prepare_mode,
    run_root_for_mode,
    write_project_report,
)


class OrchestratorModeTests(unittest.TestCase):
    def test_mode_sequence_is_nats_wiremock_jdbc_then_full(self):
        self.assertEqual(
            MODE_SEQUENCE,
            ("nats-only", "wiremock-only", "jdbc-lightweight", "full-contract-baseline"),
        )

    def test_run_root_for_mode_uses_expected_suite_directories(self):
        self.assertTrue(str(run_root_for_mode("RUN-TEST", "nats-only")).endswith("RUN-TEST/nats_capability"))
        self.assertTrue(str(run_root_for_mode("RUN-TEST", "wiremock-only")).endswith("RUN-TEST/wiremock_capability"))
        self.assertTrue(str(run_root_for_mode("RUN-TEST", "jdbc-lightweight")).endswith("RUN-TEST/jdbc_capability"))
        self.assertTrue(str(run_root_for_mode("RUN-TEST", "full-contract-baseline")).endswith("RUN-TEST/contract_baseline"))

    def test_framework_paths_are_versioned(self):
        paths = framework_paths("0.2.3")

        self.assertTrue(str(paths.jar).endswith("release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar"))
        self.assertTrue(str(paths.usage_kit_root).endswith("usage-kit-v0.2.3/usage-kit"))

    def test_framework_paths_prefer_artifacts_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            artifact_assets = repo_root / "artifacts" / "release-assets" / "release-assets-v0.2.9"
            artifact_usage_kit = repo_root / "artifacts" / "usage-kits" / "usage-kit-v0.2.9" / "usage-kit"
            legacy_assets = repo_root / "release-assets-v0.2.9"
            legacy_usage_kit = repo_root / "usage-kit-v0.2.9" / "usage-kit"
            for path in [artifact_assets, artifact_usage_kit, legacy_assets, legacy_usage_kit]:
                path.mkdir(parents=True)

            with patch("pirun.run_contract_baseline.REPO_ROOT", repo_root):
                paths = framework_paths("v0.2.9")

        self.assertEqual(
            paths.jar,
            artifact_assets / "spec-driven-auto-regression-0.2.9.jar",
        )
        self.assertEqual(paths.usage_kit_root, artifact_usage_kit)

    def test_full_mode_preserves_partial_dependency_evidence_when_later_start_fails(self):
        nats = NatsProvisionResult(
            provider_id="nats-event-bus",
            image="nats:2.10-alpine",
            container_id="nats-container",
            host="127.0.0.1",
            port=54222,
            connection_url="nats://127.0.0.1:54222",
            readiness_status="passed",
        )

        with tempfile.TemporaryDirectory() as tmp, patch(
            "pirun.run_contract_baseline.start_nats", return_value=nats
        ), patch("pirun.run_contract_baseline.start_wiremock", side_effect=RuntimeError("wiremock failed")):
            with self.assertRaises(ProvisioningError) as raised:
                prepare_mode("full-contract-baseline", "RUN-PARTIAL", "ci", Path(tmp) / "contract_baseline")

        self.assertEqual(raised.exception.failed_step, "start_wiremock")
        self.assertEqual([dependency["provider_id"] for dependency in raised.exception.dependencies], ["nats-event-bus"])

    def test_project_report_marks_wiremock_external_dependency_as_not_consumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "wiremock_capability"
            run_root.mkdir()
            (run_root / "suite_manifest.yaml").write_text("suite_id: TEST\n", encoding="utf-8")

            write_project_report(
                "RUN-WIREMOCK",
                "ci",
                "wiremock-only",
                run_root,
                [
                    {
                        "provider_id": "wiremock-payment-api",
                        "provider_type": "wiremock_http_mock",
                        "provisioner": "project_docker",
                    }
                ],
                {
                    "invoked": True,
                    "exit_code": 0,
                    "stdout": "run_status: passed\nprovider_runtime_executed: true\n",
                    "stderr": "",
                },
                {"status": "passed"},
                None,
            )

            report = json.loads((run_root / "project_report.json").read_text())

        dependency = report["dependencies"][0]
        self.assertFalse(dependency["framework_consumed"])
        self.assertEqual(
            dependency["framework_consumption_status"],
            "external_base_url_not_consumed_by_framework_provider_capability",
        )

    def test_single_provider_consumption_requires_matching_provider_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "nats_capability"
            run_root.mkdir()
            (run_root / "suite_manifest.yaml").write_text("suite_id: TEST\n", encoding="utf-8")

            write_project_report(
                "RUN-NATS",
                "ci",
                "nats-only",
                run_root,
                [{"provider_id": "local-nats-event-bus", "provider_type": "nats", "provisioner": "project_docker"}],
                {
                    "invoked": True,
                    "exit_code": 0,
                    "stdout": (
                        "run_status: passed\n"
                        "provider_runtime_executed: true\n"
                        "provider_type: nats\n"
                        "provider_id: framework-default-nats\n"
                    ),
                    "stderr": "",
                },
                {"status": "passed"},
                None,
            )

            report = json.loads((run_root / "project_report.json").read_text())

        dependency = report["dependencies"][0]
        self.assertFalse(dependency["framework_consumed"])
        self.assertEqual(dependency["framework_consumption_status"], "framework_runtime_not_confirmed")

    def test_project_report_redacts_framework_output_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "jdbc_capability"
            run_root.mkdir()
            (run_root / "suite_manifest.yaml").write_text("suite_id: TEST\n", encoding="utf-8")

            write_project_report(
                "RUN-REDACT",
                "ci",
                "jdbc-lightweight",
                run_root,
                [{"provider_id": "oracle-like-db", "provider_type": "jdbc", "provisioner": "framework_embedded_h2"}],
                {
                    "invoked": True,
                    "exit_code": 0,
                    "stdout": "run_status: passed\npassword=raw-secret-value\n",
                    "stderr": "Authorization: Bearer abc.def\n",
                },
                {"status": "passed"},
                None,
            )

            stdout = (run_root / "framework_stdout.txt").read_text()
            stderr = (run_root / "framework_stderr.txt").read_text()

        self.assertNotIn("raw-secret-value", stdout)
        self.assertNotIn("abc.def", stderr)
        self.assertIn("[REDACTED]", stdout)

    def test_project_report_distinguishes_full_contract_provider_runtime_from_external_wiremock_consumption(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "contract_baseline"
            run_root.mkdir()
            (run_root / "suite_manifest.yaml").write_text("suite_id: TEST\n", encoding="utf-8")

            write_project_report(
                "RUN-FULL",
                "ci",
                "full-contract-baseline",
                run_root,
                [
                    {"provider_id": "nats-event-bus", "provider_type": "nats", "provisioner": "project_docker"},
                    {
                        "provider_id": "wiremock-payment-api",
                        "provider_type": "wiremock_http_mock",
                        "provisioner": "project_docker",
                    },
                    {"provider_id": "oracle-database", "provider_type": "jdbc", "provisioner": "framework_embedded_h2"},
                ],
                {
                    "invoked": True,
                    "exit_code": 0,
                    "stdout": (
                        "run_status: passed\n"
                        "provider_runtime_executed: true\n"
                        "provider_ids: wiremock-payment-api,oracle-database,nats-event-bus\n"
                    ),
                    "stderr": "",
                },
                {"status": "passed"},
                None,
            )

            report = json.loads((run_root / "project_report.json").read_text())

        by_provider = {dependency["provider_id"]: dependency for dependency in report["dependencies"]}
        self.assertTrue(report["framework_consumed_project_dependencies"])
        self.assertTrue(by_provider["nats-event-bus"]["framework_consumed"])
        self.assertTrue(by_provider["oracle-database"]["framework_consumed"])
        self.assertFalse(by_provider["wiremock-payment-api"]["framework_consumed"])
        self.assertEqual(
            by_provider["wiremock-payment-api"]["framework_consumption_status"],
            "external_base_url_not_consumed_by_framework_provider_capability",
        )

    def test_project_report_survives_malformed_result_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "jdbc_capability"
            run_root.mkdir()
            (run_root / "suite_manifest.yaml").write_text("suite_id: TEST\n", encoding="utf-8")
            bad_result = root / "result.json"
            bad_result.write_text("{not-json", encoding="utf-8")

            write_project_report(
                "RUN-BAD-JSON",
                "ci",
                "jdbc-lightweight",
                run_root,
                [{"provider_id": "oracle-like-db", "provider_type": "jdbc", "provisioner": "framework_embedded_h2"}],
                {
                    "invoked": True,
                    "exit_code": 1,
                    "stdout": f"run_status: failed\nresult_json: {bad_result}\n",
                    "stderr": "framework stderr",
                },
                {"status": "passed"},
                None,
            )

            report = json.loads((run_root / "project_report.json").read_text())
            stdout = (run_root / "framework_stdout.txt").read_text()
            stderr = (run_root / "framework_stderr.txt").read_text()

        self.assertIn("result_json_parse_error", report["framework_result"])
        self.assertIn("run_status: failed", stdout)
        self.assertEqual(stderr, "framework stderr")


if __name__ == "__main__":
    unittest.main()
