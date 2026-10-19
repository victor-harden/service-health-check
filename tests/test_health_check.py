import contextlib
import io
import json
import shutil
import socket
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import health_check


class HealthCheckTests(unittest.TestCase):
    def test_tcp_open_port(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        try:
            ok, _ = health_check.check_tcp("127.0.0.1", port, timeout=1)
            self.assertTrue(ok)
        finally:
            server.close()

    def test_tcp_closed_port(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
        server.close()
        ok, detail = health_check.check_tcp("127.0.0.1", port, timeout=0.5)
        self.assertFalse(ok)
        self.assertTrue(detail)

    @unittest.skipIf(shutil.which("systemctl") is None, "systemctl unavailable")
    def test_systemd_check_returns_tuple(self):
        ok, detail = health_check.check_systemd("does-not-exist.service", timeout=5)
        self.assertFalse(ok)
        self.assertTrue(detail)

    def test_unknown_check_type(self):
        results = health_check.run_checks({"checks": [{"name": "x", "type": "dns"}]})
        self.assertFalse(results[0]["ok"])

    def test_run_checks_tcp(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        try:
            results = health_check.run_checks(
                {"checks": [{"name": "local", "type": "tcp", "host": "127.0.0.1", "port": port}]}
            )
            self.assertTrue(results[0]["ok"])
        finally:
            server.close()

    def test_render(self):
        text = health_check.render([{"name": "a", "type": "tcp", "ok": True, "detail": "connected"}])
        self.assertIn("[OK]", text)

    def test_cli_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "checks.json"
            server = socket.socket()
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            config.write_text(json.dumps(
                {"checks": [{"name": "local", "type": "tcp", "host": "127.0.0.1", "port": port}]}
            ))
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    code = health_check.main([str(config), "--json"])
                self.assertEqual(code, 0)
                payload = json.loads(buf.getvalue())
                self.assertTrue(payload[0]["ok"])
            finally:
                server.close()


if __name__ == "__main__":
    unittest.main()
