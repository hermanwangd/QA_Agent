import tempfile
import unittest
from pathlib import Path

import yaml

from pirun.materialize.contract_baseline import (
    materialize_heavy_jdbc_container,
    materialize_heavy_jdbc_crud_container,
)


class HeavyJdbcMaterializeTests(unittest.TestCase):
    def test_materialize_oracle_project_jdbc_uses_native_runtime_and_env_binding_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_oracle_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="oracle-like-db",
                dialect="oracle",
                connection_secret_ref="env://JDBC_CONNECTION",
                profile="ci",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            execution_profile = run_dir / "execution_profiles" / "ci.yaml"
            test_case = run_dir / "test_case.yaml"
            project_binding = run_dir / "project_bindings" / "oracle-like-db.yaml"

            combined = "\n".join(p.read_text() for p in [env_binding, env_profile, execution_profile, test_case])
            self.assertIn("env://JDBC_CONNECTION", combined)
            self.assertIn("dialect: oracle", combined)
            self.assertIn("provider_instance_ref: provider_instances/oracle_like.yaml", combined)
            self.assertIn("runtime_mode: native", combined)
            self.assertIn("allowed_runtime_modes:\n  - native", combined)
            self.assertIn("allowed_provisioners:\n  - project_docker", combined)
            self.assertIn("project_provisioned_dependency: docker_jdbc_oracle", combined)
            self.assertNotIn("generated://", combined)
            self.assertNotIn("runtime_mode: external", combined)
            self.assertTrue(project_binding.exists())

    def test_materialize_db2_project_jdbc_uses_db2_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_db2_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="db2-like-db",
                dialect="db2",
                connection_secret_ref="env://JDBC_CONNECTION",
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
            self.assertEqual(provider_binding["runtime_mode"], "native")
            self.assertEqual(provider_binding["binding_values"]["dialect"], "db2")
            self.assertEqual(provider_binding["binding_values"]["connection"]["secret_ref"], "env://JDBC_CONNECTION")
            self.assertIn("project_sql_probe", combined)

    def test_materialize_db2_retargets_test_case_and_writes_db2_seed_sql(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_db2_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="db2-like-db",
                dialect="db2",
                connection_secret_ref="env://JDBC_CONNECTION",
                profile="ci",
            )

            test_case = yaml.safe_load((run_dir / "test_case.yaml").read_text())
            seed_sql = (run_dir / "fixtures" / "db_seed.sql").read_text()

        self.assertEqual(test_case["targets"], {"db2_like_db": {"provider_id": "db2-like-db"}})
        self.assertEqual(test_case["setup"]["operations"][0]["target"], "db2_like_db")
        self.assertEqual(test_case["execute"]["operations"][0]["target"], "db2_like_db")
        self.assertEqual(
            test_case["execute"]["operations"][0]["inputs"]["query_ref"]["ref"],
            "queries/order_exists_db2.sql",
        )
        self.assertEqual(test_case["verify"]["checks"][0]["target"], "db2_like_db")
        self.assertEqual(test_case["verify"]["checks"][0]["query"]["ref"], "queries/order_exists_db2.sql")
        self.assertEqual(test_case["cleanup"]["operations"][0]["target"], "db2_like_db")
        self.assertIn("merge into ORDERS as t", seed_sql)
        self.assertNotIn("create table if not exists", seed_sql)

    def test_materialize_oracle_writes_real_oracle_seed_sql(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_oracle_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="oracle-like-db",
                dialect="oracle",
                connection_secret_ref="env://JDBC_CONNECTION",
                profile="ci",
            )

            seed_sql = (run_dir / "fixtures" / "db_seed.sql").read_text()

        self.assertIn("merge into ORDERS t", seed_sql)
        self.assertIn("from dual", seed_sql)
        self.assertNotIn("create table if not exists", seed_sql)

    def test_materialize_oracle_crud_suite_has_explicit_create_read_update_delete_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_oracle_crud_container"
            materialize_heavy_jdbc_crud_container(
                run_dir=run_dir,
                provider_id="oracle-like-db",
                dialect="oracle",
                connection_secret_ref="env://JDBC_CONNECTION",
                profile="ci",
            )

            test_case = yaml.safe_load((run_dir / "test_case.yaml").read_text())
            execute_ops = test_case["execute"]["operations"]
            execute_ids = [operation["id"] for operation in execute_ops]
            execute_operation_types = {operation["id"]: operation["operation"] for operation in execute_ops}
            verify_check = test_case["verify"]["checks"][0]

            self.assertEqual(test_case["test_case_id"], "JDBC-CRUD-TC-001")
            self.assertEqual(
                execute_ids,
                [
                    "create_order",
                    "read_created_order",
                    "update_order",
                    "read_updated_order",
                    "delete_order",
                    "read_deleted_order",
                ],
            )
            self.assertEqual(execute_operation_types["create_order"], "db_seed")
            self.assertEqual(execute_operation_types["read_created_order"], "db_query")
            self.assertEqual(execute_operation_types["update_order"], "db_seed")
            self.assertEqual(execute_operation_types["read_updated_order"], "db_query")
            self.assertEqual(execute_operation_types["delete_order"], "db_cleanup")
            self.assertEqual(execute_operation_types["read_deleted_order"], "db_query")
            self.assertIn("provider-evidence/jdbc/seed_create_order.yaml", test_case["evidence"]["required"])
            self.assertIn("provider-evidence/jdbc/query_read_updated_order.yaml", test_case["evidence"]["required"])
            self.assertIn("provider-evidence/jdbc/cleanup_delete_order.yaml", test_case["evidence"]["required"])
            self.assertEqual(verify_check["id"], "deleted_order_record_absent")
            self.assertEqual(verify_check["query"]["ref"], "queries/crud_order_by_id_oracle.sql")
            self.assertEqual(verify_check["expected_ref"], "expected_results/crud_deleted_expected.json")

            insert_sql = (run_dir / "fixtures" / "crud_insert_order.sql").read_text()
            update_sql = (run_dir / "fixtures" / "crud_update_order.sql").read_text()
            delete_sql = (run_dir / "fixtures" / "crud_delete_order.sql").read_text()
            query_sql = (run_dir / "queries" / "crud_order_by_id_oracle.sql").read_text()
            deleted_expected = yaml.safe_load((run_dir / "expected_results" / "crud_deleted_expected.json").read_text())

        self.assertIn("insert into ORDERS", insert_sql)
        self.assertIn("'CREATED'", insert_sql)
        self.assertIn("update ORDERS", update_sql)
        self.assertIn("'UPDATED'", update_sql)
        self.assertIn("delete from ORDERS", delete_sql)
        self.assertIn("select ORDER_ID, STATUS", query_sql)
        self.assertEqual(deleted_expected["expected_row_count"], 0)


if __name__ == "__main__":
    unittest.main()
