import json
import tempfile
import unittest
from pathlib import Path

from pirun.inspect_usage_kit import inspect_usage_kit, write_matrix_reports
from pirun.run_contract_baseline import framework_paths


class UsageKitInspectorTests(unittest.TestCase):
    def setUp(self):
        self.usage_kit_root = framework_paths("0.2.3").usage_kit_root

    def test_registry_provider_runtime_modes_are_accounted_for(self):
        inspection = inspect_usage_kit(self.usage_kit_root)
        rows = inspection["matrix_rows"]

        self.assertEqual(inspection["summary"]["registry_without_contract"], [])
        self.assertIn("sample_fake_provider", inspection["summary"]["contracts_without_registry"])
        self.assertIn("common_verify", inspection["summary"]["contracts_without_registry"])

        provider_types = {row["provider_type"] for row in rows}
        self.assertIn("nats", provider_types)
        self.assertIn("wiremock_http_mock", provider_types)
        self.assertIn("kafka", provider_types)
        self.assertIn("ibm_mq", provider_types)

        kafka_native = _row(rows, "kafka", "native")
        kafka_ephemeral = _row(rows, "kafka", "ephemeral")
        kafka_mock = _row(rows, "kafka", "mock")
        self.assertEqual(kafka_native["expected_status"], "BLOCKED_FRAMEWORK_CONTRACT_ONLY")
        self.assertEqual(kafka_ephemeral["expected_status"], "BLOCKED_FRAMEWORK_CONTRACT_ONLY")
        self.assertEqual(kafka_mock["expected_status"], "PASS")
        self.assertTrue(kafka_mock["direct_sample"])

        ibm_native = _row(rows, "ibm_mq", "native")
        ibm_ephemeral = _row(rows, "ibm_mq", "ephemeral")
        self.assertEqual(ibm_native["expected_status"], "BLOCKED_FRAMEWORK_CONTRACT_ONLY")
        self.assertEqual(ibm_ephemeral["expected_status"], "BLOCKED_FRAMEWORK_CONTRACT_ONLY")

    def test_command_capable_providers_without_samples_are_sample_gaps_not_safety_blocked(self):
        rows = inspect_usage_kit(self.usage_kit_root)["matrix_rows"]

        for provider_type, runtime_mode in [
            ("shell_command", "native"),
            ("external_runner", "native"),
            ("kubernetes_runtime", "native"),
            ("vm_runtime", "native"),
        ]:
            row = _row(rows, provider_type, runtime_mode)
            self.assertEqual(row["expected_status"], "BLOCKED_USAGE_KIT_SAMPLE_GAP")
            self.assertFalse(row["runnable_now"])
            self.assertIn("sample", row["reason"])

    def test_sample_coverage_is_runtime_mode_specific(self):
        rows = inspect_usage_kit(self.usage_kit_root)["matrix_rows"]

        rest_native = _row(rows, "rest_client", "native")
        rest_stub = _row(rows, "rest_client", "stub")
        nats_mock = _row(rows, "nats", "mock")
        nats_ephemeral = _row(rows, "nats", "ephemeral")

        self.assertEqual(rest_native["expected_status"], "PASS")
        self.assertEqual(rest_stub["expected_status"], "BLOCKED_USAGE_KIT_SAMPLE_GAP")
        self.assertFalse(rest_stub["runnable_now"])
        self.assertEqual(nats_mock["expected_status"], "PASS")
        self.assertEqual(nats_ephemeral["expected_status"], "PASS")

    def test_non_runnable_rows_have_blocked_statuses_and_reasons(self):
        rows = inspect_usage_kit(self.usage_kit_root)["matrix_rows"]

        for row in rows:
            if row["runnable_now"]:
                continue
            self.assertTrue(
                row["expected_status"].startswith("BLOCKED_"),
                f"{row['provider_type']}/{row['runtime_mode']} uses {row['expected_status']}",
            )
            self.assertTrue(row["reason"].strip(), f"{row['provider_type']}/{row['runtime_mode']} has no reason")

        kafka_alias = _row(rows, "kafka_messaging", "mock")
        self.assertEqual(kafka_alias["expected_status"], "BLOCKED_DEPRECATED_ALIAS")

    def test_deprecated_support_status_is_classified_as_deprecated_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_dir = root / "docs/02-architecture/contracts"
            contract_dir = registry_dir / "provider-contracts"
            contract_dir.mkdir(parents=True)
            (registry_dir / "provider_capability_registry.v0.2.yaml").write_text(
                """
provider_types:
  kafka_messaging:
    contract_ref: provider-contracts/kafka_messaging.yaml
    support_status: deprecated
    supported_runtime_modes: [native, mock, ephemeral]
""".lstrip(),
                encoding="utf-8",
            )
            (contract_dir / "kafka_messaging.yaml").write_text(
                """
provider_contract_version: v0.2
provider_type: kafka_messaging
status: deprecated_alias
runtime_modes: [native, mock, ephemeral]
""".lstrip(),
                encoding="utf-8",
            )

            rows = inspect_usage_kit(root)["matrix_rows"]

        for runtime_mode in ("native", "mock", "ephemeral"):
            self.assertEqual(
                _row(rows, "kafka_messaging", runtime_mode)["expected_status"],
                "BLOCKED_DEPRECATED_ALIAS",
            )

    def test_contract_only_support_status_is_classified_as_framework_contract_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_dir = root / "docs/02-architecture/contracts"
            contract_dir = registry_dir / "provider-contracts"
            contract_dir.mkdir(parents=True)
            (registry_dir / "provider_capability_registry.v0.2.yaml").write_text(
                """
provider_types:
  shell_command:
    contract_ref: provider-contracts/shell_command.yaml
    support_status: contract_only
    supported_runtime_modes: [native, mock, stub]
""".lstrip(),
                encoding="utf-8",
            )
            (contract_dir / "shell_command.yaml").write_text(
                """
provider_contract_version: v0.2
provider_type: shell_command
status: contract_only
runtime_modes: [native, mock, stub]
""".lstrip(),
                encoding="utf-8",
            )

            rows = inspect_usage_kit(root)["matrix_rows"]

        for runtime_mode in ("native", "mock", "stub"):
            self.assertEqual(
                _row(rows, "shell_command", runtime_mode)["expected_status"],
                "BLOCKED_FRAMEWORK_CONTRACT_ONLY",
            )

    def test_report_and_validate_evidence_release_command_gaps_are_reported(self):
        inspection = inspect_usage_kit(self.usage_kit_root)

        self.assertIn("report", inspection["summary"]["missing_release_verification_commands"])
        self.assertIn("validate-evidence", inspection["summary"]["missing_release_verification_commands"])
        self.assertIn("run", inspection["summary"]["present_release_verification_commands"])
        self.assertIn("validate", inspection["summary"]["present_release_verification_commands"])

    def test_matrix_reports_are_written_as_json_and_markdown(self):
        inspection = inspect_usage_kit(self.usage_kit_root)

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_matrix_reports(inspection, Path(tmp), version="0.2.3")
            payload = json.loads(outputs["json"].read_text())
            markdown = outputs["markdown"].read_text()

        self.assertGreater(payload["summary"]["matrix_row_count"], 0)
        self.assertIn("| Provider Type | Runtime Mode |", markdown)
        self.assertIn("BLOCKED_FRAMEWORK_CONTRACT_ONLY", markdown)
        self.assertNotIn("BLOCKED_SAFETY_POLICY", markdown)


def _row(rows, provider_type, runtime_mode):
    for row in rows:
        if row["provider_type"] == provider_type and row["runtime_mode"] == runtime_mode:
            return row
    raise AssertionError(f"missing row: {provider_type}/{runtime_mode}")


if __name__ == "__main__":
    unittest.main()
