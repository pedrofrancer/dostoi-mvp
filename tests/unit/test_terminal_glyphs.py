"""Unidade (TechSpecs Seção 57): expressão conhecida vira glifo
próprio, desconhecida cai pro neutro sem quebrar."""
import unittest

from visual_harness.terminal.glyphs import NEUTRAL_GLYPH, glyph_for


class TestGlyphFor(unittest.TestCase):
    def test_known_expression_has_its_own_glyph(self):
        self.assertEqual(glyph_for("curious"), "(o_O)")
        self.assertNotEqual(glyph_for("curious"), NEUTRAL_GLYPH)

    def test_neutral_expression_is_the_neutral_glyph(self):
        self.assertEqual(glyph_for("neutral"), NEUTRAL_GLYPH)

    def test_unknown_expression_falls_back_to_neutral(self):
        self.assertEqual(glyph_for("expressao-que-nao-existe-ainda"), NEUTRAL_GLYPH)


if __name__ == "__main__":
    unittest.main()
