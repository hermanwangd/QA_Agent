import tempfile
import unittest
from pathlib import Path

import yaml

from pirun.materialize.contract_baseline import (
    materialize_full_contract_baseline,
    materialize_jdbc_lightweight,
    materialize_nats_only,
    materialize_wiremock_only,
)


class MaterializeTests(unittest.TestCase):
    def test_materialize_nats_only_writes_standard_artifacts_without_generated_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "contract_baseline"
            materialize_nats_only(
                run_dir=run_dir,
                nats_subject="payments.accepted",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            execution_profile = run_dir / "execution_profiles" / "ci.yaml"
            suite = run_dir / "suite_manifest.yaml"
            test_case = run_dir / "test_case.yaml"

            self.assertTrue(env_binding.exists())
            self.assertTrue(env_profile.exists())
            self.assertTrue(execution_profile.exists())
            self.assertTrue(suite.exists())
            self.assertFalse((run_dir / "environment_bindings" / "local_nats.yaml").exists())

            combined = "\n".join(p.read_text() for p in [env_binding, env_profile, execution_profile, suite, test_case])
            self.assertNotIn("generated://", combined)
            self.assertIn("env://PIRUN_NATS_CONNECTION", combined)
            self.assertIn("provider_id: local-nats-event-bus", env_binding.read_text())
            self.assertIn("profile: ci", env_binding.read_text())
            self.assertIn("compatible_profiles:\n- ci", test_case.read_text())

    def test_materialize_wiremock_only_writes_project_base_url_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "wiremock_capability"
            materialize_wiremock_only(
                run_dir=run_dir,
                base_url="http://127.0.0.1:58080",
                profile="ci",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            test_case = run_dir / "test_case.yaml"
            project_binding = run_dir / "project_bindings" / "wiremock-payment-api.yaml"

            self.assertTrue(env_binding.exists())
            self.assertTrue(env_profile.exists())
            self.assertTrue(project_binding.exists())
            self.assertFalse((run_dir / "environment_bindings" / "local_wiremock.yaml").exists())

            combined = "\n".join(p.read_text() for p in [env_binding, env_profile, test_case])
            self.assertNotIn("generated://wiremock-payment-api.base_url", combined)
            self.assertNotIn("base_url: http://127.0.0.1:58080", combined)
            self.assertIn("base_url: http://127.0.0.1:58080", project_binding.read_text())
            self.assertIn(
                "framework_consumption_status: external_base_url_not_consumed_by_framework_provider_capability",
                project_binding.read_text(),
            )
            self.assertIn("allowed_provisioners:\n  - project_docker", combined)
            self.assertIn("project_provisioned_dependency: docker_wiremock", combined)

    def test_materialize_jdbc_lightweight_uses_generated_h2_ref_without_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_capability"
            materialize_jdbc_lightweight(
                run_dir=run_dir,
                connection_secret_ref="generated://provider-capability/oracle-like/connection",
                profile="ci",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            test_case = run_dir / "test_case.yaml"

            combined = "\n".join(p.read_text() for p in [env_binding, env_profile, test_case])
            self.assertIn("generated://provider-capability/oracle-like/connection", combined)
            self.assertIn("allowed_provisioners:\n  - framework_embedded_h2", combined)
            self.assertIn("project_provisioned_dependency: framework_embedded_h2", combined)
            self.assertNotIn("oracle_database_container", combined)

    def test_materialize_full_contract_baseline_writes_three_provider_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "contract_baseline"
            materialize_full_contract_baseline(
                run_dir=run_dir,
                nats_connection_secret_ref="env://PIRUN_NATS_CONNECTION",
                wiremock_base_url="http://127.0.0.1:58080",
                jdbc_connection_secret_ref="generated://provider-capability/oracle-like/connection",
                profile="ci",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            test_case = run_dir / "test_case.yaml"
            project_binding = run_dir / "project_bindings" / "wiremock-payment-api.yaml"
            wiremock_mapping = run_dir / "fixtures" / "wiremock" / "payment-api" / "mappings.yaml"
            sql_query = run_dir / "fixtures" / "sql" / "find_order.sql"

            combined = "\n".join(p.read_text() for p in [env_binding, test_case])
            self.assertIn("provider_id: wiremock-payment-api", combined)
            self.assertIn("provider_id: oracle-database", combined)
            self.assertIn("provider_id: nats-event-bus", combined)
            self.assertNotIn("base_url: http://127.0.0.1:58080", combined)
            self.assertIn("base_url: http://127.0.0.1:58080", project_binding.read_text())
            self.assertIn(
                "framework_consumption_status: external_base_url_not_consumed_by_framework_provider_capability",
                project_binding.read_text(),
            )
            self.assertIn("env://PIRUN_NATS_CONNECTION", combined)
            self.assertTrue(wiremock_mapping.exists())
            self.assertTrue(sql_query.exists())
            mapping_payload = yaml.safe_load(wiremock_mapping.read_text())
            self.assertIn("stubs", mapping_payload)
            self.assertEqual(mapping_payload["stubs"][0]["request"]["path"], "/payments")


if __name__ == "__main__":
    unittest.main()
