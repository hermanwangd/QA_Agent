import tempfile
import unittest
from pathlib import Path

from pirun.scan_raw_secrets import scan_paths, write_secret_scan_report


class RawSecretScanTests(unittest.TestCase):
    def test_secret_refs_are_allowed_but_raw_password_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe = root / "safe.json"
            unsafe = root / "unsafe.txt"
            safe.write_text('{"connection": {"secret_ref": "env://SAFE_REF"}}\n', encoding="utf-8")
            unsafe.write_text("password=raw-secret-value\n", encoding="utf-8")

            report = scan_paths([root])

        self.assertEqual(report["raw_secret_scan"], "FAIL")
        self.assertIn("password_assignment", {finding["pattern"] for finding in report["findings"]})

    def test_json_and_yaml_secret_key_values_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unsafe.json").write_text(
                '{"password": "super-secret-123", "token": "abc.def"}\n',
                encoding="utf-8",
            )
            (root / "unsafe.yaml").write_text(
                "api_key: plain-text-api-key\nsecret: plain-text-secret\n",
                encoding="utf-8",
            )

            report = scan_paths([root])

        self.assertEqual(report["raw_secret_scan"], "FAIL")
        self.assertIn("secret_key_value", {finding["pattern"] for finding in report["findings"]})

    def test_secret_scan_report_writes_markdown(self):
        report = {
            "raw_secret_scan": "PASS",
            "scanned_file_count": 1,
            "findings": [],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_secret_scan_report(report, Path(tmp), version="0.2.3")
            markdown = outputs["markdown"].read_text()

        self.assertIn("Raw secret scan: `PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
