import tempfile
import unittest
from pathlib import Path

from pirun.verify_release_assets import verify_release_assets, write_release_asset_report


class ReleaseAssetVerificationTests(unittest.TestCase):
    def test_checksum_passes_and_signature_is_not_available_without_sig_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = Path(tmp)
            artifact = asset_dir / "artifact.bin"
            artifact.write_text("hello\n", encoding="utf-8")
            checksum = "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
            (asset_dir / "checksums.sha256").write_text(f"{checksum}  target/artifact.bin\n", encoding="utf-8")

            report = verify_release_assets(asset_dir)

        self.assertFalse(report["source_archive_used"])
        self.assertEqual(report["checksum_verification"], "PASS")
        self.assertEqual(report["signature_verification"], "NOT_AVAILABLE")
        self.assertEqual(report["assets"][0]["checksum_status"], "PASS")

    def test_release_asset_report_writes_json_and_markdown(self):
        report = {
            "release_asset_verification_version": "v0.1",
            "source_archive_used": False,
            "checksum_verification": "PASS",
            "signature_verification": "NOT_AVAILABLE",
            "assets": [
                {
                    "name": "artifact.bin",
                    "checksum_status": "PASS",
                    "signature_status": "NOT_AVAILABLE",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_release_asset_report(report, Path(tmp), version="0.2.3")
            self.assertTrue(outputs["json"].exists())
            markdown = outputs["markdown"].read_text()

        self.assertIn("Checksum verification: `PASS`", markdown)
        self.assertIn("Signature verification: `NOT_AVAILABLE`", markdown)


if __name__ == "__main__":
    unittest.main()
