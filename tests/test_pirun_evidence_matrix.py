import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pirun.run_contract_baseline import framework_paths
from pirun.run_evidence_matrix import build_evidence_cases, run_evidence_matrix, write_evidence_matrix_report


class EvidenceMatrixTests(unittest.TestCase):
    def test_evidence_cases_include_positive_negative_and_report_json_gap_probe(self):
        cases = build_evidence_cases()
        ids = {case["id"] for case in cases}

        self.assertIn("validate-evidence-valid", ids)
        self.assertIn("validate-evidence-missing-evidence", ids)
        self.assertIn("validate-evidence-secret-leak", ids)
        self.assertIn("report-valid-text", ids)
        self.assertIn("report-valid-yaml", ids)
        self.assertIn("report-valid-json", ids)

    def test_runner_uses_low_memory_java_and_classifies_expected_failures(self):
        paths = framework_paths("0.2.3")
        cases = [
            {
                "id": "positive",
                "command": ["validate-evidence", "--result", "valid.json"],
                "expected_exit": 0,
                "category": "validate-evidence-positive",
            },
            {
                "id": "negative",
                "command": ["validate-evidence", "--result", "invalid.json"],
                "expected_exit": 1,
                "category": "validate-evidence-negative",
            },
        ]
        returns = [
            Mock(returncode=0, stdout="evidence_validation_status: passed\n", stderr=""),
            Mock(returncode=1, stdout="evidence_validation_status: failed\n", stderr=""),
        ]

        with patch("pirun.run_evidence_matrix.subprocess.run", side_effect=returns) as run:
            report = run_evidence_matrix(cases, framework_jar=paths.jar, usage_kit_root=paths.usage_kit_root)

        self.assertEqual([result["status"] for result in report["results"]], ["PASS", "EXPECTED_FAIL"])
        for call in run.call_args_list:
            self.assertEqual(call.args[0][0:3], ["java", "-Xmx512m", "-jar"])

    def test_summary_separates_supported_report_gates_from_unsupported_json_probe(self):
        paths = framework_paths("0.2.3")
        cases = [
            {
                "id": "report-valid-text",
                "command": ["report", "--result", "valid.json", "--format", "text"],
                "expected_exit": 0,
                "category": "report-positive",
            },
            {
                "id": "report-missing-evidence-text",
                "command": ["report", "--result", "invalid.json", "--format", "text"],
                "expected_exit": 1,
                "category": "report-negative",
            },
            {
                "id": "report-valid-yaml",
                "command": ["report", "--result", "valid.json", "--format", "yaml"],
                "expected_exit": 0,
                "category": "report-positive",
            },
            {
                "id": "report-missing-evidence-yaml",
                "command": ["report", "--result", "invalid.json", "--format", "yaml"],
                "expected_exit": 1,
                "category": "report-negative",
            },
            {
                "id": "report-valid-json",
                "command": ["report", "--result", "valid.json", "--format", "json"],
                "expected_exit": 0,
                "category": "report-positive",
            },
        ]
        returns = [
            Mock(returncode=0, stdout="report_status: review_ready\n", stderr=""),
            Mock(returncode=1, stdout="report_status: failed\n", stderr=""),
            Mock(returncode=0, stdout="report_status: review_ready\n", stderr=""),
            Mock(returncode=1, stdout="report_status: failed\n", stderr=""),
            Mock(returncode=2, stdout="", stderr="Unsupported --format: json\n"),
        ]

        with patch("pirun.run_evidence_matrix.subprocess.run", side_effect=returns):
            report = run_evidence_matrix(cases, framework_jar=paths.jar, usage_kit_root=paths.usage_kit_root)

        by_id = {result["id"]: result for result in report["results"]}
        self.assertEqual(by_id["report-valid-json"]["status"], "BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT")
        self.assertEqual(report["summary"]["report_supported_positive_status"], "PASS")
        self.assertEqual(report["summary"]["report_supported_negative_status"], "EXPECTED_FAIL")
        self.assertEqual(report["summary"]["blocked_framework_count"], 1)

    def test_report_gate_fails_when_required_supported_format_is_missing(self):
        paths = framework_paths("0.2.3")
        cases = [
            {
                "id": "report-valid-text",
                "command": ["report", "--result", "valid.json", "--format", "text"],
                "expected_exit": 0,
                "category": "report-positive",
            }
        ]

        with patch("pirun.run_evidence_matrix.subprocess.run", return_value=Mock(returncode=0, stdout="", stderr="")):
            report = run_evidence_matrix(cases, framework_jar=paths.jar, usage_kit_root=paths.usage_kit_root)

        self.assertEqual(report["summary"]["report_supported_positive_status"], "FAIL")
        self.assertEqual(report["summary"]["report_supported_positive_missing_formats"], ["yaml"])

    def test_runner_redacts_raw_secrets_from_captured_output(self):
        paths = framework_paths("0.2.3")
        cases = [
            {
                "id": "validate-evidence-valid",
                "command": ["validate-evidence", "--result", "valid.json"],
                "expected_exit": 0,
                "category": "validate-evidence-positive",
            }
        ]
        completed = Mock(
            returncode=0,
            stdout="report_status: ok\npassword=raw-secret-value\n",
            stderr="Authorization: Bearer abc.def\n",
        )

        with patch("pirun.run_evidence_matrix.subprocess.run", return_value=completed):
            report = run_evidence_matrix(cases, framework_jar=paths.jar, usage_kit_root=paths.usage_kit_root)

        self.assertNotIn("raw-secret-value", report["results"][0]["stdout"])
        self.assertNotIn("abc.def", report["results"][0]["stderr"])
        self.assertIn("[REDACTED]", report["results"][0]["stdout"])

    def test_evidence_matrix_report_writes_markdown(self):
        report = {
            "summary": {
                "case_count": 1,
                "pass_count": 1,
                "expected_fail_count": 0,
                "blocked_framework_count": 0,
                "unexpected_fail_count": 0,
                "report_supported_positive_status": "PASS",
                "report_supported_positive_missing_formats": [],
                "report_supported_negative_status": "NOT_RUN",
                "report_supported_negative_missing_formats": ["text", "yaml"],
                "validate_evidence_positive_status": "NOT_RUN",
                "validate_evidence_negative_status": "NOT_RUN",
            },
            "results": [
                {
                    "id": "report-valid-text",
                    "status": "PASS",
                    "exit_code": 0,
                    "expected_exit": 0,
                    "category": "report-positive",
                    "stdout": "report_status: review_ready",
                    "stderr": "",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_evidence_matrix_report(report, Path(tmp), version="0.2.3")
            markdown = outputs["markdown"].read_text()

        self.assertIn("report-valid-text", markdown)
        self.assertIn("PASS", markdown)


if __name__ == "__main__":
    unittest.main()
