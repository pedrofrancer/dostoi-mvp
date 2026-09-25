"""Unidade (TechSpecs Seção 60.1, 43, 62): fallback de template quando
não há LLM, redação do contexto antes da chamada, e a guarda de
vocabulário mesmo em cima do que o LLM devolveria.
"""
import unittest
from unittest.mock import MagicMock, patch

from visual_harness.judgment import judge


class TestFallbackComment(unittest.TestCase):
    def test_test_failure_without_llm_uses_template(self):
        with patch("visual_harness.judgment.judge._client", return_value=None):
            texto, source = judge.comment("test_failure", {"command": "pytest"})
        self.assertEqual(source, "heuristica")
        self.assertIn("pytest", texto)

    def test_rework_without_llm_uses_template(self):
        with patch("visual_harness.judgment.judge._client", return_value=None):
            texto, source = judge.comment(
                "rework", {"path": "src/auth.py", "seconds_since": 10.0}
            )
        self.assertEqual(source, "heuristica")
        self.assertIn("src/auth.py", texto)

    def test_unknown_checkpoint_type_has_a_safe_default(self):
        with patch("visual_harness.judgment.judge._client", return_value=None):
            texto, source = judge.comment("outro", {})
        self.assertEqual(source, "heuristica")
        self.assertTrue(texto)


class TestRedactionBeforeEgress(unittest.TestCase):
    def test_secret_in_context_never_reaches_the_llm_call(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="comentario qualquer")]
        )
        with patch("visual_harness.judgment.judge._client", return_value=mock_client):
            judge.comment("test_failure", {"command": "curl -H 'TOKEN=abc123' https://x"})

        sent_message = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
        self.assertNotIn("abc123", sent_message)
        self.assertIn("[REDACTED]", sent_message)


class TestVocabularyGuardOnLlmOutput(unittest.TestCase):
    def test_llm_output_with_banned_claim_falls_back_to_template(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="estou com medo desse teste")]
        )
        with patch("visual_harness.judgment.judge._client", return_value=mock_client):
            texto, source = judge.comment("test_failure", {"command": "pytest"})

        self.assertEqual(source, "heuristica")
        self.assertNotIn("medo", texto)

    def test_llm_output_within_vocabulary_passes_through(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="essa funcao ja apareceu antes nessa sessao")]
        )
        with patch("visual_harness.judgment.judge._client", return_value=mock_client):
            texto, source = judge.comment("rework", {"path": "a.py", "seconds_since": 5.0})

        self.assertEqual(source, "llm")
        self.assertEqual(texto, "essa funcao ja apareceu antes nessa sessao")


if __name__ == "__main__":
    unittest.main()
