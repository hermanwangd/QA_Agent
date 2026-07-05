import unittest
from unittest.mock import patch

from pirun.docker_cli import CommandResult
from pirun.provisioners.wiremock import start_wiremock, wait_for_http


class FakeResponse:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class WireMockProvisionerTests(unittest.TestCase):
    def test_start_wiremock_pulls_image_and_exposes_base_url(self):
        calls = []

        def fake_run_command(cmd, timeout=60):
            calls.append((cmd, timeout))
            if cmd[1] == "pull":
                return CommandResult(0, "pulled\n", "")
            if cmd[1] == "run":
                return CommandResult(0, "wiremock-container\n", "")
            if cmd[1] == "port":
                return CommandResult(0, "127.0.0.1:58080\n", "")
            raise AssertionError(f"unexpected command: {cmd}")

        with patch("pirun.provisioners.wiremock.run_command", side_effect=fake_run_command), patch(
            "pirun.provisioners.wiremock.wait_for_http"
        ):
            result = start_wiremock("RUN-TEST")

        self.assertEqual(result.provider_id, "wiremock-payment-api")
        self.assertEqual(result.base_url, "http://127.0.0.1:58080")
        self.assertEqual(result.readiness_status, "passed")
        self.assertEqual(calls[0][0][1], "pull")
        self.assertIn("wiremock/wiremock", calls[0][0][-1])
        self.assertEqual(calls[1][0][1], "run")
        self.assertIn("pirun.suite=wiremock_capability", calls[1][0])
        self.assertIn("--memory", calls[1][0])
        self.assertIn("512m", calls[1][0])

    def test_wait_for_http_ignores_client_errors_until_success(self):
        with patch(
            "pirun.provisioners.wiremock.urllib.request.urlopen",
            side_effect=[FakeResponse(404), FakeResponse(200)],
        ) as urlopen, patch("pirun.provisioners.wiremock.time.sleep"):
            wait_for_http("http://127.0.0.1:58080/__admin", timeout_seconds=1)

        self.assertEqual(urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
