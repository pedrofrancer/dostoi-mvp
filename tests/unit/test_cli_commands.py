import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from visual_harness.cli.commands import app

runner = CliRunner()


class TestStatus(unittest.TestCase):
    @patch("visual_harness.cli.commands.httpx.get")
    def test_reports_running(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "ok", "version": "0.1.0", "uptime": 12.3, "connected_adapters": 0},
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = runner.invoke(app, ["status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("rodando", result.output)

    @patch("visual_harness.cli.commands.httpx.get")
    def test_reports_not_running_on_connection_error(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("recusado")

        result = runner.invoke(app, ["status"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("não está rodando", result.output)


class TestEvent(unittest.TestCase):
    def test_requires_type_without_json(self):
        result = runner.invoke(app, ["event"])
        self.assertEqual(result.exit_code, 2)

    @patch("visual_harness.cli.commands.httpx.post")
    def test_flag_mode_builds_correct_body(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        result = runner.invoke(
            app,
            ["event", "--type", "file_read", "--path", "src/main.py", "--session", "s1"],
        )
        self.assertEqual(result.exit_code, 0)

        _, kwargs = mock_post.call_args
        body = kwargs["json"]
        self.assertEqual(body["type"], "file_read")
        self.assertEqual(body["session_id"], "s1")
        self.assertEqual(body["payload"]["path"], "src/main.py")

    @patch("visual_harness.cli.commands.httpx.post")
    def test_json_mode_sends_body_verbatim(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        raw = {"session_id": "s1", "source": "cli", "type": "test_failed", "payload": {"test": "x"}}

        result = runner.invoke(app, ["event", "--json", json.dumps(raw)])
        self.assertEqual(result.exit_code, 0)

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"], raw)

    @patch("visual_harness.cli.commands.httpx.post")
    def test_server_rejection_exits_nonzero(self, mock_post):
        mock_post.return_value = MagicMock(status_code=422, text="payload invalido")

        result = runner.invoke(app, ["event", "--type", "file_read", "--path", "a.py"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("rejeitado", result.output)


class TestDemo(unittest.TestCase):
    @patch("visual_harness.cli.commands.httpx.post")
    def test_default_hits_start_endpoint(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"state": "running"})
        mock_post.return_value.raise_for_status = lambda: None

        runner.invoke(app, ["demo"])
        url = mock_post.call_args[0][0]
        self.assertTrue(url.endswith("/api/demo/start"))

    @patch("visual_harness.cli.commands.httpx.post")
    def test_stop_flag_hits_stop_endpoint(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"state": "idle"})
        mock_post.return_value.raise_for_status = lambda: None

        runner.invoke(app, ["demo", "--stop"])
        url = mock_post.call_args[0][0]
        self.assertTrue(url.endswith("/api/demo/stop"))


class TestStop(unittest.TestCase):
    def test_without_pidfile_reports_and_exits_nonzero(self):
        with TemporaryDirectory() as tmp:
            fake_pid_file = Path(tmp) / "nao-existe" / "server.pid"
            with patch("visual_harness.cli.commands.PID_FILE", fake_pid_file):
                result = runner.invoke(app, ["stop"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("nenhum servidor registrado", result.output)


class TestStart(unittest.TestCase):
    @patch("visual_harness.cli.commands.uvicorn.run")
    def test_writes_pidfile_during_run_and_removes_after(self, mock_run):
        with TemporaryDirectory() as tmp:
            fake_pid_file = Path(tmp) / "sub" / "server.pid"

            def assert_pidfile_exists_while_running(*_args, **_kwargs):
                self.assertTrue(fake_pid_file.exists())

            mock_run.side_effect = assert_pidfile_exists_while_running

            with patch("visual_harness.cli.commands.PID_FILE", fake_pid_file):
                result = runner.invoke(app, ["start"])

            self.assertEqual(result.exit_code, 0)
            self.assertFalse(fake_pid_file.exists())


if __name__ == "__main__":
    unittest.main()
