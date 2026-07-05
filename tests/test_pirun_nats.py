import unittest
from unittest.mock import patch

from pirun.docker_cli import CommandResult
from pirun.provisioners.nats import start_nats


class NatsProvisionerTests(unittest.TestCase):
    def test_start_nats_pulls_image_before_run(self):
        calls = []

        def fake_run_command(cmd, timeout=60):
            calls.append((cmd, timeout))
            if cmd[1] == "pull":
                return CommandResult(0, "pulled\n", "")
            if cmd[1] == "run":
                return CommandResult(0, "container-123\n", "")
            if cmd[1] == "port":
                return CommandResult(0, "127.0.0.1:42222\n", "")
            raise AssertionError(f"unexpected command: {cmd}")

        with patch("pirun.provisioners.nats.run_command", side_effect=fake_run_command), patch(
            "pirun.provisioners.nats.wait_for_tcp"
        ):
            result = start_nats("RUN-TEST")

        self.assertEqual(result.connection_url, "nats://127.0.0.1:42222")
        self.assertEqual(calls[0][0][1], "pull")
        self.assertEqual(calls[0][0][-1], "nats:2.10-alpine")
        self.assertGreaterEqual(calls[0][1], 300)
        self.assertEqual(calls[1][0][1], "run")
        self.assertIn("pirun.suite=nats_capability", calls[1][0])


if __name__ == "__main__":
    unittest.main()
