"""Unidade (TechSpecs Seção 60.1, 43, 62): fallback de template quando
não há LLM configurado, redação do contexto antes da chamada, e a
guarda de vocabulário mesmo em cima do que o LLM devolveria. O cliente
é HTTP genérico compatível com OpenAI (Groq, OpenRouter, Ollama local,
etc.), não um SDK de provedor específico.
"""
import unittest
from unittest.mock import MagicMock, patch

from visual_harness.judgment import judge

_NO_PROVIDER = {"VH_JUDGE_BASE_URL": "", "VH_JUDGE_API_KEY": "", "VH_JUDGE_MODEL": ""}
_FAKE_PROVIDER = {
    "VH_JUDGE_BASE_URL": "https://api.exemplo.com/v1",
    "VH_JUDGE_API_KEY": "chave-fake",
    "VH_JUDGE_MODEL": "modelo-fake",
}


def _fake_response(content: str):
    response = MagicMock()
    response.raise_for_status = lambda: None
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


class TestFallbackComment(unittest.TestCase):
    def test_test_failure_without_provider_uses_template(self):
        with patch.dict("os.environ", _NO_PROVIDER):
            texto, source = judge.comment("test_failure", {"command": "pytest"})
        self.assertEqual(source, "heuristica")
        self.assertIn("pytest", texto)

    def test_rework_without_provider_uses_template(self):
        with patch.dict("os.environ", _NO_PROVIDER):
            texto, source = judge.comment(
                "rework", {"path": "src/auth.py", "seconds_since": 10.0}
            )
        self.assertEqual(source, "heuristica")
        self.assertIn("src/auth.py", texto)

    def test_unknown_checkpoint_type_has_a_safe_default(self):
        with patch.dict("os.environ", _NO_PROVIDER):
            texto, source = judge.comment("outro", {})
        self.assertEqual(source, "heuristica")
        self.assertTrue(texto)

    def test_provider_partially_configured_uses_template(self):
        partial = {**_NO_PROVIDER, "VH_JUDGE_BASE_URL": "https://api.exemplo.com/v1"}
        with patch.dict("os.environ", partial):
            texto, source = judge.comment("test_failure", {"command": "pytest"})
        self.assertEqual(source, "heuristica")


class TestGenericOpenAiCompatibleCall(unittest.TestCase):
    def test_posts_to_chat_completions_with_bearer_token(self):
        with patch.dict("os.environ", _FAKE_PROVIDER):
            with patch("httpx.post", return_value=_fake_response("comentario qualquer")) as post:
                texto, source = judge.comment("test_failure", {"command": "pytest"})

        self.assertEqual(source, "llm")
        self.assertEqual(texto, "comentario qualquer")
        url = post.call_args.args[0]
        kwargs = post.call_args.kwargs
        self.assertEqual(url, "https://api.exemplo.com/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer chave-fake")
        self.assertEqual(kwargs["json"]["model"], "modelo-fake")

    def test_provider_unreachable_falls_back_to_template(self):
        with patch.dict("os.environ", _FAKE_PROVIDER):
            with patch("httpx.post", side_effect=OSError("sem rede")):
                texto, source = judge.comment("test_failure", {"command": "pytest"})
        self.assertEqual(source, "heuristica")


class TestRedactionBeforeEgress(unittest.TestCase):
    def test_secret_in_context_never_reaches_the_llm_call(self):
        with patch.dict("os.environ", _FAKE_PROVIDER):
            with patch("httpx.post", return_value=_fake_response("comentario qualquer")) as post:
                judge.comment("test_failure", {"command": "curl -H 'TOKEN=abc123' https://x"})

        sent_message = post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertNotIn("abc123", sent_message)
        self.assertIn("[REDACTED]", sent_message)


class TestVocabularyGuardOnLlmOutput(unittest.TestCase):
    def test_llm_output_with_banned_claim_falls_back_to_template(self):
        with patch.dict("os.environ", _FAKE_PROVIDER):
            with patch("httpx.post", return_value=_fake_response("estou com medo desse teste")):
                texto, source = judge.comment("test_failure", {"command": "pytest"})

        self.assertEqual(source, "heuristica")
        self.assertNotIn("medo", texto)

    def test_llm_output_within_vocabulary_passes_through(self):
        with patch.dict("os.environ", _FAKE_PROVIDER):
            with patch(
                "httpx.post",
                return_value=_fake_response("essa funcao ja apareceu antes nessa sessao"),
            ):
                texto, source = judge.comment("rework", {"path": "a.py", "seconds_since": 5.0})

        self.assertEqual(source, "llm")
        self.assertEqual(texto, "essa funcao ja apareceu antes nessa sessao")


if __name__ == "__main__":
    unittest.main()
