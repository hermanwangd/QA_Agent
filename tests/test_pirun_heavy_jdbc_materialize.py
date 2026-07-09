import tempfile
import unittest
from pathlib import Path

import yaml

from pirun.materialize.contract_baseline import materialize_heavy_jdbc_container


class HeavyJdbcMaterializeTests(unittest.TestCase):
    def test_materialize_oracle_external_jdbc_uses_env_binding_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_oracle_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="oracle-like-db",
                dialect="oracle",
                connection_secret_ref="env://PIRUN_JDBC_CONNECTION",
                profile="ci",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            execution_profile = run_dir / "execution_profiles" / "ci.yaml"
            test_case = run_dir / "test_case.yaml"
            project_binding = run_dir / "project_bindings" / "oracle-like-db.yaml"

            combined = "\n".join(p.read_text() for p in [env_binding, env_profile, execution_profile, test_case])
            self.assertIn("env://PIRUN_JDBC_CONNECTION", combined)
            self.assertIn("dialect: oracle", combined)
            self.assertIn("provider_instance_ref: provider_instances/oracle_like.yaml", combined)
            self.assertIn("allowed_provisioners:\n  - project_docker", combined)
            self.assertIn("project_provisioned_dependency: docker_jdbc_oracle", combined)
            self.assertNotIn("generated://", combined)
            self.assertTrue(project_binding.exists())

    def test_materialize_db2_external_jdbc_uses_db2_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_db2_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="db2-like-db",
                dialect="db2",
                connection_secret_ref="env://PIRUN_JDBC_CONNECTION",
                profile="ci",
            )

            env_binding = yaml.safe_load((run_dir / "environment_bindings" / "ci.yaml").read_text())
            provider_binding = env_binding["provider_bindings"][0]
            combined = "\n".join(
                p.read_text()
                for p in [
                    run_dir / "environment_bindings" / "ci.yaml",
                    run_dir / "env_profiles" / "ci.yaml",
                    run_dir / "execution_profiles" / "ci.yaml",
                ]
            )

            self.assertEqual(provider_binding["provider_id"], "db2-like-db")
            self.assertEqual(provider_binding["provider_instance_ref"], "provider_instances/db2_like.yaml")
            self.assertEqual(provider_binding["runtime_mode"], "external")
            self.assertEqual(provider_binding["binding_values"]["dialect"], "db2")
            self.assertEqual(provider_binding["binding_values"]["connection"]["secret_ref"], "env://PIRUN_JDBC_CONNECTION")
            self.assertIn("project_sql_probe", combined)


if __name__ == "__main__":
    unittest.main()
