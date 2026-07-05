import unittest

from pirun.docker_cli import build_docker_run_command, docker_subprocess_env


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


if __name__ == "__main__":
    unittest.main()
