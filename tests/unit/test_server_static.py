import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore


class TestStaticMount(unittest.TestCase):
    def test_static_index_is_served_and_api_routes_still_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            static_dir = Path(tmp)
            (static_dir / "index.html").write_text("<h1>avatar aqui</h1>", encoding="utf-8")

            bus = EventBus()
            store = SessionStore()
            demo_player = DemoPlayer(bus, step_delay_s=0.01)
            app = create_app(bus, store, demo_player, static_dir=static_dir)
            client = TestClient(app)

            index_response = client.get("/")
            self.assertEqual(index_response.status_code, 200)
            self.assertIn("avatar aqui", index_response.text)

            health_response = client.get("/api/health")
            self.assertEqual(health_response.status_code, 200)
            self.assertEqual(health_response.json()["status"], "ok")

    def test_no_static_dir_means_no_mount_and_api_still_works(self):
        bus = EventBus()
        store = SessionStore()
        demo_player = DemoPlayer(bus, step_delay_s=0.01)
        app = create_app(bus, store, demo_player, static_dir=None)
        client = TestClient(app)

        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
