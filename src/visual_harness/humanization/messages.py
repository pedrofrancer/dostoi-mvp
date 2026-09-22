"""Vocabulário de mensagem (TechSpecs Seção 62): o sistema não reivindica
experiência subjetiva, só descreve o observável. "Reconsiderando
abordagem", nunca "a IA está com medo".
"""

FORBIDDEN_SUBSTRINGS = (
    "com medo",
    "com raiva",
    "sofrendo",
    "consciente",
    "consciência",
    " sente ",
    "sentindo",
)


def check_message(message: str | None) -> None:
    if message is None:
        return
    lowered = f" {message.lower()} "
    for forbidden in FORBIDDEN_SUBSTRINGS:
        if forbidden in lowered:
            raise ValueError(
                f"mensagem viola o vocabulário da Seção 62 "
                f"(contém {forbidden.strip()!r}): {message!r}"
            )
