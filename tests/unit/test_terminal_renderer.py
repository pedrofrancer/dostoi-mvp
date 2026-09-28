"""Unidade (TechSpecs Seção 18-19, 57-59): o overlay reserva a região
com DECSTBM, desenha só quando o conteúdo muda, o popup de Camada 2
volta pro último estado quando some, e cada modo (compact/full/minimal)
mostra o que deve.
"""
import io
import unittest

from visual_harness.terminal import ansi
from visual_harness.terminal.renderer import (
    MODE_FULL,
    MODE_MINIMAL,
    TerminalOverlay,
    _context_lines,
    _layer2_box,
    _sanitize,
    _state_box,
    _timeline_lines,
)


def _overlay(mode="compact", rows=24):
    stream = io.StringIO()
    overlay = TerminalOverlay(stream=stream, mode=mode, rows=rows)
    return overlay, stream


class TestStartAndStop(unittest.TestCase):
    def test_start_reserves_the_bottom_rows(self):
        overlay, stream = _overlay(mode="compact", rows=24)
        overlay.start()
        output = stream.getvalue()
        self.assertIn(ansi.set_scroll_region(1, 18), output)  # 24 - region(6)
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


class TestMinimalMode(unittest.TestCase):
    def test_shows_only_the_glyph(self):
        overlay, stream = _overlay(mode=MODE_MINIMAL)
        overlay.start()
        overlay.render_state({"state": "reconsidering", "humanization": {"expression": "thoughtful"}})
        output = stream.getvalue()
        self.assertIn("(u_u)", output)
        self.assertNotIn("Reconsidering", output)


class TestFullMode(unittest.TestCase):
    def test_state_context_and_timeline_all_appear(self):
        overlay, stream = _overlay(mode=MODE_FULL)
        overlay.start()
        overlay.render_state({"state": "testing", "humanization": {"expression": "focused"}})
        overlay.render_context(
            {
                "context": {
                    "task": "Authentication",
                    "agent": "Claude Code",
                    "modified_files": ["a.py", "b.py"],
                    "tests_passed": 31,
                    "tests_failed": 2,
                    "recent_errors": ["x"],
                }
            }
        )
        overlay.render_timeline_entry({"transition": {"to": "understanding"}})
        overlay.render_timeline_entry({"transition": {"to": "testing"}})

        output = stream.getvalue()
        self.assertIn("Testing", output)
        self.assertIn("Authentication", output)
        self.assertIn("Claude Code", output)
        self.assertIn("2 modificados", output)
        self.assertIn("31 / 2", output)
        self.assertIn("Understanding", output)
        # a mais recente marcada diferente das que ja passaram (Secao 18)
        self.assertIn("→ Testing", output)
        self.assertIn("✓ Understanding", output)

    def test_timeline_is_capped_at_five_entries(self):
        overlay, stream = _overlay(mode=MODE_FULL)
        overlay.start()
        for i in range(8):
            overlay.render_timeline_entry({"transition": {"to": f"state{i}"}})
        self.assertEqual(len(overlay._timeline_labels), 5)
        self.assertEqual(overlay._timeline_labels[0], "State3")
        self.assertEqual(overlay._timeline_labels[-1], "State7")


class TestSessionLock(unittest.TestCase):
    def test_first_session_locks_out_messages_from_other_sessions(self):
        overlay, stream = _overlay()
        overlay.start()
        overlay.render_state(
            {"session_id": "s1", "state": "idle", "humanization": {"expression": "neutral"}}
        )
        stream.truncate(0)
        stream.seek(0)

        overlay.render_state(
            {"session_id": "s2", "state": "testing", "humanization": {"expression": "focused"}}
        )

        self.assertEqual(stream.getvalue(), "")  # sessao errada, nada desenhado


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


class TestControlCharacterSanitization(unittest.TestCase):
    """task/agent/mensagem de Camada 2 vem de payload de evento, fora
    do controle do processo (Step 19): sem isso, um payload malicioso
    escreve sequência de escape ANSI de verdade no terminal de quem
    roda `vh watch` (troca de título, reposicionamento de cursor)."""

    _INJECTION = "normal\x1b]0;pwned\x07resto"

    def test_sanitize_strips_c0_and_del(self):
        self.assertEqual(_sanitize(self._INJECTION), "normal]0;pwnedresto")
        self.assertEqual(_sanitize("a\x7fb"), "ab")

    def test_context_lines_strip_control_chars_from_task_and_agent(self):
        lines = _context_lines(
            {"task": self._INJECTION, "agent": self._INJECTION}, inner_width=40
        )
        joined = "\n".join(lines)
        self.assertNotIn("\x1b", joined)
        self.assertNotIn("\x07", joined)

    def test_layer2_box_strips_control_chars_from_message(self):
        lines = _layer2_box(self._INJECTION)
        joined = "\n".join(lines)
        self.assertNotIn("\x1b", joined)
        self.assertNotIn("\x07", joined)

    def test_timeline_lines_strip_control_chars_from_label(self):
        lines = _timeline_lines([self._INJECTION], inner_width=40)
        joined = "\n".join(lines)
        self.assertNotIn("\x1b", joined)
        self.assertNotIn("\x07", joined)

    def test_state_box_strips_control_chars_from_state(self):
        lines = _state_box(self._INJECTION, "neutral")
        joined = "\n".join(lines)
        self.assertNotIn("\x1b", joined)
        self.assertNotIn("\x07", joined)


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
