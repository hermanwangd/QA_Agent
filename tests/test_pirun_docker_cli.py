import unittest

from pirun.docker_cli import build_docker_exec_command, build_docker_run_command, docker_subprocess_env


class DockerCliTests(unittest.TestCase):
    def test_build_nats_run_command_has_labels_and_limits(self):
        cmd = build_docker_run_command(
            run_id="RUN-TEST",
            suite="contract_baseline",
            name="pirun-RUN-TEST-nats",
            image="nats:2.10-alpine",
            ports={"4222/tcp": 0},
            memory="256m",
        )

        joined = " ".join(cmd)
        self.assertIn("/usr/local/bin/docker", cmd[0])
        self.assertIn("--label", cmd)
        self.assertIn("pirun.run_id=RUN-TEST", cmd)
        self.assertIn("pirun.suite=contract_baseline", cmd)
        self.assertIn("--memory", cmd)
        self.assertIn("256m", cmd)
        self.assertIn("nats:2.10-alpine", cmd)
        self.assertIn("-p", cmd)
        self.assertIn("127.0.0.1::4222", joined)

    def test_docker_subprocess_env_includes_docker_desktop_helpers(self):
        env = docker_subprocess_env()

        self.assertIn("/Applications/Docker.app/Contents/Resources/bin", env["PATH"])
        self.assertIn("/usr/local/bin", env["PATH"])
        self.assertEqual(env["DOCKER_CONFIG"], "/tmp/pirun-docker-config")

    def test_build_run_command_supports_env_shm_and_privileged_option(self):
        cmd = build_docker_run_command(
            run_id="RUN-HEAVY",
            suite="jdbc_oracle_container",
            name="pirun-RUN-HEAVY-oracle",
            image="gvenzl/oracle-free:23-slim-faststart",
            ports={"1521/tcp": 0},
            memory="3g",
            env={
                "ORACLE_PASSWORD": "Secret-12345",
                "APP_USER": "APP",
                "APP_USER_PASSWORD": "Secret-12345",
            },
            shm_size="1g",
            privileged=False,
        )

        joined = " ".join(cmd)
        self.assertIn("--shm-size", cmd)
        self.assertIn("1g", cmd)
        self.assertIn("--env", cmd)
        self.assertIn("ORACLE_PASSWORD=Secret-12345", cmd)
        self.assertIn("APP_USER=APP", cmd)
        self.assertIn("APP_USER_PASSWORD=Secret-12345", cmd)
        self.assertNotIn("--privileged", cmd)
        self.assertIn("127.0.0.1::1521", joined)

    def test_build_run_command_supports_db2_privileged_mode(self):
        cmd = build_docker_run_command(
            run_id="RUN-DB2",
            suite="jdbc_db2_container",
            name="pirun-RUN-DB2-db2",
            image="icr.io/db2_community/db2",
            ports={"50000/tcp": 0},
            memory="6g",
            env={"LICENSE": "accept", "DB2INSTANCE": "db2inst1", "DBNAME": "testdb"},
            privileged=True,
        )

        self.assertIn("--privileged", cmd)
        self.assertIn("--env", cmd)
        self.assertIn("LICENSE=accept", cmd)
        self.assertIn("DB2INSTANCE=db2inst1", cmd)
        self.assertIn("DBNAME=testdb", cmd)

    def test_docker_exec_command_uses_configured_binary(self):
        cmd = build_docker_exec_command("pirun-RUN-db", ["bash", "-lc", "echo ok"])

        self.assertEqual(cmd[:3], ["/usr/local/bin/docker", "exec", "pirun-RUN-db"])
        self.assertEqual(cmd[3:], ["bash", "-lc", "echo ok"])


if __name__ == "__main__":
    unittest.main()
