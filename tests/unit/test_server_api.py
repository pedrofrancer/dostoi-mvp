import unittest

from fastapi.testclient import TestClient

from visual_harness.demo.player import DemoPlayer
from visual_harness.events.bus import EventBus
from visual_harness.server.api import create_app
from visual_harness.server.store import SessionStore


def build_test_app():
    bus = EventBus()
    store = SessionStore()
    demo_player = DemoPlayer(bus, step_delay_s=0.01)
    app = create_app(bus, store, demo_player)
    return app, bus, store, demo_player


class TestHealth(unittest.TestCase):
    def test_health_returns_ok_and_version(self):
        app, *_ = build_test_app()
        client = TestClient(app)
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("version", body)
        self.assertEqual(body["connected_adapters"], 0)


class TestSessionsAndEvents(unittest.TestCase):
    def test_post_event_creates_session_and_is_listed(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        response = client.post(
            "/api/events",
            json={
                "session_id": "sess_1",
                "source": "claude-code",
                "type": "task_started",
                "payload": {"description": "algo"},
            },
        )
        self.assertEqual(response.status_code, 200)

        sessions = client.get("/api/sessions").json()
        self.assertEqual([s["id"] for s in sessions], ["sess_1"])

        events = client.get("/api/sessions/sess_1/events").json()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "task_started")

    def test_get_session_includes_context(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        client.post(
            "/api/events",
            json={
                "session_id": "sess_1",
                "source": "claude-code",
                "type": "task_started",
                "payload": {"description": "Implementar X"},
            },
        )

        session = client.get("/api/sessions/sess_1").json()
        self.assertIn("context", session)
        self.assertEqual(session["context"]["task"], "Implementar X")
        self.assertEqual(session["context"]["current_state"], "understanding")

    def test_unknown_session_returns_404(self):
        app, *_ = build_test_app()
        client = TestClient(app)
        response = client.get("/api/sessions/nao-existe")
        self.assertEqual(response.status_code, 404)

    def test_invalid_event_type_is_rejected(self):
        app, *_ = build_test_app()
        client = TestClient(app)
        response = client.post(
            "/api/events",
            json={"session_id": "s", "source": "x", "type": "tipo_inventado"},
        )
        self.assertEqual(response.status_code, 422)

    def test_timeline_shows_state_transitions(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        for event_type, payload in (
            ("task_started", {"description": "algo"}),
            ("test_failed", {"test": "login"}),
            ("approach_changed", {}),
        ):
            client.post(
                "/api/events",
                json={
                    "session_id": "sess_1",
                    "source": "claude-code",
                    "type": event_type,
                    "payload": payload,
                },
            )

        timeline = client.get("/api/sessions/sess_1/timeline").json()
        transitions = [(t["from"], t["to"]) for t in timeline]
        self.assertEqual(
            transitions,
            [
                (None, "understanding"),
                ("understanding", "error"),
                ("error", "reconsidering"),
            ],
        )


class TestDemoEndpoints(unittest.TestCase):
    def test_demo_start_then_stop_changes_state(self):
        app, _bus, _store, demo_player = build_test_app()
        client = TestClient(app)

        response = client.post("/api/demo/start")
        self.assertEqual(response.json()["state"], "running")

        response = client.post("/api/demo/stop")
        self.assertEqual(response.json()["state"], "idle")


class TestWebSocket(unittest.TestCase):
    def test_websocket_receives_event_and_state_update(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            post_response = client.post(
                "/api/events",
                json={
                    "session_id": "sess_ws",
                    "source": "claude-code",
                    "type": "task_started",
                    "payload": {"description": "algo"},
                },
            )
            self.assertEqual(post_response.status_code, 200)

            first = websocket.receive_json()
            second = websocket.receive_json()

        self.assertEqual(first["type"], "event")
        self.assertEqual(first["payload"]["type"], "task_started")
        self.assertEqual(second["type"], "state_update")
        self.assertEqual(second["payload"]["state"], "understanding")

    def test_malformed_websocket_message_does_not_drop_connection(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("isso nao e json")
            websocket.send_bytes(b"\x00\x01binario")
            websocket.send_json(["nao", "e", "um", "dict"])

            # a conexao segue viva: um evento de verdade ainda chega normal
            client.post(
                "/api/events",
                json={
                    "session_id": "sess_ws_bad",
                    "source": "claude-code",
                    "type": "task_started",
                    "payload": {},
                },
            )
            message = websocket.receive_json()

        self.assertEqual(message["type"], "event")

    def test_rapid_state_changes_are_debounced_in_broadcast(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            client.post(
                "/api/events",
                json={
                    "session_id": "sess_hyst",
                    "source": "claude-code",
                    "type": "task_started",
                    "payload": {"description": "algo"},
                },
            )
            websocket.receive_json()  # event
            first_state_update = websocket.receive_json()
            websocket.receive_json()  # timeline_update (None -> understanding, transicao real)
            websocket.receive_json()  # session_update

            # segundo evento chega bem rapido (dentro da janela padrao de 200ms)
            client.post(
                "/api/events",
                json={
                    "session_id": "sess_hyst",
                    "source": "claude-code",
                    "type": "test_failed",
                    "payload": {"test": "login"},
                },
            )
            websocket.receive_json()  # event
            second_state_update = websocket.receive_json()
            websocket.receive_json()  # timeline_update (understanding -> error, transicao real)
            websocket.receive_json()  # session_update

        self.assertEqual(first_state_update["payload"]["state"], "understanding")
        # a mudanca de verdade (error) fica suprimida pela histerese;
        # o que aparece no state_update ainda e o estado anterior
        self.assertEqual(second_state_update["payload"]["state"], "understanding")

    def test_websocket_receives_timeline_update_on_real_transition(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            client.post(
                "/api/events",
                json={
                    "session_id": "sess_ws2",
                    "source": "claude-code",
                    "type": "task_started",
                    "payload": {"description": "algo"},
                },
            )
            websocket.receive_json()  # event
            websocket.receive_json()  # state_update
            third = websocket.receive_json()

        self.assertEqual(third["type"], "timeline_update")
        self.assertIsNone(third["payload"]["transition"]["from"])
        self.assertEqual(third["payload"]["transition"]["to"], "understanding")

    def test_websocket_receives_session_update_with_the_current_context(self):
        app, *_ = build_test_app()
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            client.post(
                "/api/events",
                json={
                    "session_id": "sess_ctx",
                    "source": "claude-code",
                    "type": "task_started",
                    "payload": {"description": "corrigir login"},
                },
            )
            websocket.receive_json()  # event
            websocket.receive_json()  # state_update
            websocket.receive_json()  # timeline_update
            fourth = websocket.receive_json()

        self.assertEqual(fourth["type"], "session_update")
        self.assertEqual(fourth["payload"]["session_id"], "sess_ctx")
        self.assertEqual(fourth["payload"]["context"]["task"], "corrigir login")
        self.assertEqual(fourth["payload"]["context"]["agent"], "claude-code")


class TestDefaultBind(unittest.TestCase):
    def test_default_host_is_localhost_not_all_interfaces(self):
        from visual_harness.main import DEFAULT_HOST

        self.assertEqual(DEFAULT_HOST, "127.0.0.1")
        self.assertNotEqual(DEFAULT_HOST, "0.0.0.0")


if __name__ == "__main__":
    unittest.main()
