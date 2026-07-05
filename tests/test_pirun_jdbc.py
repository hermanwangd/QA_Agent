import unittest

from pirun.provisioners.jdbc import start_jdbc_lightweight


class JdbcProvisionerTests(unittest.TestCase):
    def test_start_jdbc_lightweight_uses_framework_generated_h2_without_container(self):
        result = start_jdbc_lightweight("RUN-TEST")

        self.assertEqual(result.provider_id, "oracle-like-db")
        self.assertEqual(result.provider_type, "jdbc")
        self.assertEqual(result.runtime_mode, "ephemeral")
        self.assertEqual(result.provisioner, "framework_embedded_h2")
        self.assertEqual(result.dialect, "oracle")
        self.assertEqual(result.connection_secret_ref, "generated://provider-capability/oracle-like/connection")
        self.assertIsNone(result.container_id)
        self.assertEqual(result.readiness_status, "delegated_to_framework")


if __name__ == "__main__":
    unittest.main()
