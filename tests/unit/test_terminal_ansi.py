"""Unidade: as sequências VT/ANSI são texto puro, então o teste é
comparação exata de string, sem terminal de verdade envolvido.
"""
import unittest

from visual_harness.terminal import ansi


class TestCursorAndRegionSequences(unittest.TestCase):
    def test_save_and_restore_are_decsc_decrc(self):
        self.assertEqual(ansi.SAVE_CURSOR, "\x1b7")
        self.assertEqual(ansi.RESTORE_CURSOR, "\x1b8")

    def test_move_to_is_one_indexed_row_col(self):
        self.assertEqual(ansi.move_to(3, 10), "\x1b[3;10H")

    def test_set_scroll_region(self):
        self.assertEqual(ansi.set_scroll_region(1, 20), "\x1b[1;20r")

    def test_reset_scroll_region(self):
        self.assertEqual(ansi.reset_scroll_region(), "\x1b[r")

    def test_hide_and_show_cursor(self):
        self.assertEqual(ansi.HIDE_CURSOR, "\x1b[?25l")
        self.assertEqual(ansi.SHOW_CURSOR, "\x1b[?25h")


class TestForegroundColor(unittest.TestCase):
    def test_known_color_wraps_text_in_sgr_and_reset(self):
        self.assertEqual(ansi.fg("red", "erro"), "\x1b[31merro\x1b[0m")

    def test_unknown_color_falls_back_to_default(self):
        self.assertEqual(ansi.fg("roxo-inventado", "x"), f"\x1b[39mx{ansi.RESET}")


if __name__ == "__main__":
    unittest.main()
