"""Unidade (TechSpecs Seção 18, 57-59): o overlay reserva a região com
DECSTBM, desenha só quando o conteúdo muda, e o popup de Camada 2 volta
pro último estado quando some.
"""
import io
import unittest

from visual_harness.terminal import ansi
from visual_harness.terminal.renderer import TerminalOverlay


def _overlay(region_height=4, rows=24):
    stream = io.StringIO()
    overlay = TerminalOverlay(stream=stream, region_height=region_height, rows=rows)
    return overlay, stream


class TestStartAndStop(unittest.TestCase):
    def test_start_reserves_the_bottom_rows(self):
        overlay, stream = _overlay(region_height=4, rows=24)
        overlay.start()
        output = stream.getvalue()
        self.assertIn(ansi.set_scroll_region(1, 20), output)
        self.assertIn(ansi.HIDE_CURSOR, output)

    def test_stop_resets_the_scroll_region_and_shows_the_cursor(self):
        overlay, stream = _overlay()
        overlay.start()
        stream.truncate(0)
        stream.seek(0)
        overlay.stop()
        output = stream.getvalue()
        self.assertIn(ansi.reset_scroll_region(), output)
        self.assertIn(ansi.SHOW_CURSOR, output)

    def test_stop_before_start_does_not_write_anything(self):
        overlay, stream = _overlay()
        overlay.stop()
        self.assertEqual(stream.getvalue(), "")


class TestRenderState(unittest.TestCase):
    def test_state_and_glyph_appear_in_the_reserved_region(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_state({"state": "reconsidering", "humanization": {"expression": "thoughtful"}})
        output = stream.getvalue()
        self.assertIn("Reconsidering", output)
        self.assertIn("(u_u)", output)

    def test_identical_state_is_not_redrawn(self):
        overlay, stream = _overlay()
        overlay.start()
        payload = {"state": "idle", "humanization": {"expression": "neutral"}}
        overlay.render_state(payload)
        stream.truncate(0)
        stream.seek(0)
        overlay.render_state(dict(payload))
        self.assertEqual(stream.getvalue(), "")

    def test_changed_state_is_redrawn(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_state({"state": "idle", "humanization": {"expression": "neutral"}})
        stream.truncate(0)
        stream.seek(0)
        overlay.render_state({"state": "testing", "humanization": {"expression": "focused"}})
        self.assertIn("Testing", stream.getvalue())


class TestLayer2Popup(unittest.TestCase):
    def test_layer2_message_appears_in_the_region(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_layer2({"message": "essa funcao ja apareceu antes"})
        self.assertIn("essa funcao ja apareceu antes", stream.getvalue())

    def test_clear_layer2_reverts_to_the_last_state(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_state({"state": "testing", "humanization": {"expression": "focused"}})
        overlay.render_layer2({"message": "comentario transitorio"})
        stream.truncate(0)
        stream.seek(0)

        overlay.clear_layer2()

        output = stream.getvalue()
        self.assertIn("Testing", output)
        self.assertNotIn("comentario transitorio", output)

    def test_clear_layer2_without_prior_state_does_not_crash(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_layer2({"message": "primeiro checkpoint da sessao"})
        overlay.clear_layer2()  # nao deve levantar, mesmo sem state_update antes


class TestReconnecting(unittest.TestCase):
    def test_reconnecting_shows_the_delay(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_reconnecting(4)
        output = stream.getvalue()
        self.assertIn("Connection lost", output)
        self.assertIn("4s", output)


if __name__ == "__main__":
    unittest.main()
