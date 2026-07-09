import tempfile
import unittest
from pathlib import Path

from pirun.provisioners.heavy_jdbc import (
    BYTES_PER_GIB,
    HeavyJdbcLock,
    evaluate_resource_gate,
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


if __name__ == "__main__":
    unittest.main()
