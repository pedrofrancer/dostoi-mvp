import unittest

from visual_harness.privacy.redaction import REDACTED, redact_payload, redact_text


class TestRedactText(unittest.TestCase):
    def test_api_key_is_redacted(self):
        result = redact_text("rodei com API_KEY=sk-abcd1234")
        self.assertIn(REDACTED, result)
        self.assertNotIn("sk-abcd1234", result)

    def test_key_name_stays_visible(self):
        result = redact_text("API_KEY=sk-abcd1234")
        self.assertTrue(result.startswith("API_KEY="))

    def test_password_is_redacted(self):
        result = redact_text("PASSWORD=hunter2 no log")
        self.assertNotIn("hunter2", result)

    def test_token_with_colon_is_redacted(self):
        result = redact_text("TOKEN: abc.def.ghi")
        self.assertNotIn("abc.def.ghi", result)

    def test_private_key_pem_block_is_redacted(self):
        pem = (
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvQIBADANBgkqhkiG9w0BAQ==\n"
            "-----END PRIVATE KEY-----"
        )
        result = redact_text(f"chave: {pem}")
        self.assertNotIn("MIIEvQIBADANBgkqhkiG9w0BAQ==", result)
        self.assertIn(REDACTED, result)

    def test_plain_text_without_secret_is_unchanged(self):
        text = "lendo src/main.py e rodando pytest"
        self.assertEqual(redact_text(text), text)

    def test_case_insensitive_key_name(self):
        result = redact_text("api_key=segredo123")
        self.assertNotIn("segredo123", result)


class TestRedactPayload(unittest.TestCase):
    def test_redacts_nested_dict_values(self):
        payload = {"env": {"API_KEY": "nao importa a chave em si"}, "command": "API_KEY=abc123 npm start"}
        result = redact_payload(payload)
        self.assertNotIn("abc123", result["command"])

    def test_redacts_values_inside_lists(self):
        payload = {"lines": ["normal", "TOKEN=segredo-xyz"]}
        result = redact_payload(payload)
        self.assertNotIn("segredo-xyz", result["lines"][1])

    def test_non_string_values_untouched(self):
        payload = {"count": 42, "ok": True, "ratio": 0.5}
        self.assertEqual(redact_payload(payload), payload)


if __name__ == "__main__":
    unittest.main()
