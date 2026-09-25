"""Unidade (TechSpecs Seção 32, 58): o dispatch roteia cada tipo de
mensagem pro método certo do overlay, e o popup de Camada 2 some
sozinho depois do tempo configurado.
"""
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from visual_harness.terminal import client


class TestBackoff(unittest.TestCase):
    def test_matches_the_browser_clients_backoff(self):
        self.assertEqual(client.BACKOFF_STEPS_SECONDS, (1, 2, 4, 8, 16, 30))


class TestDispatch(unittest.TestCase):
    def test_state_update_calls_render_state(self):
        overlay = MagicMock()
        client.dispatch(overlay, {"type": "state_update", "payload": {"state": "idle"}})
        overlay.render_state.assert_called_once_with({"state": "idle"})

    def test_unknown_type_touches_nothing(self):
        overlay = MagicMock()
        client.dispatch(overlay, {"type": "session_update", "payload": {}})
        overlay.render_state.assert_not_called()
        overlay.render_layer2.assert_not_called()

    def test_missing_payload_defaults_to_empty_dict(self):
        overlay = MagicMock()
        client.dispatch(overlay, {"type": "state_update"})
        overlay.render_state.assert_called_once_with({})


class TestLayer2AutoClear(unittest.IsolatedAsyncioTestCase):
    async def test_layer2_update_renders_then_clears_after_the_window(self):
        overlay = MagicMock()
        with patch.object(client, "LAYER2_POPUP_SECONDS", 0.01):
            task = client.dispatch(
                overlay, {"type": "layer2_update", "payload": {"message": "retrabalho"}}
            )
            self.assertIsNotNone(task)
            await task

        overlay.render_layer2.assert_called_once_with({"message": "retrabalho"})
        overlay.clear_layer2.assert_called_once()

    async def test_cancelling_the_task_skips_the_clear(self):
        overlay = MagicMock()
        with patch.object(client, "LAYER2_POPUP_SECONDS", 10):
            task = client.dispatch(
                overlay, {"type": "layer2_update", "payload": {"message": "x"}}
            )
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        overlay.clear_layer2.assert_not_called()


if __name__ == "__main__":
    unittest.main()
