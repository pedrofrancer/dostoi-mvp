"""Pele mínima embutida (TechSpecs Seção 30-31): um glifo por
`Expression`, não o grid de partes (olhos/sobrancelha/boca) que a Seção
30 descreve pro sistema de peles completo — esse fica pro modo cheio,
depois que o compacto provar que a redação em cima do checkpoint faz
sentido no terminal (mesma ordem que o resto do projeto seguiu).
"""
from visual_harness.humanization.expressions import Expression

NEUTRAL_GLYPH = "(-_-)"

_GLYPH_BY_EXPRESSION: dict[Expression, str] = {
    Expression.NEUTRAL: NEUTRAL_GLYPH,
    Expression.FOCUSED: "(°_°)",
    Expression.CURIOUS: "(o_O)",
    Expression.THOUGHTFUL: "(u_u)",
    Expression.CONCERNED: "(>_<)",
    Expression.SURPRISED: "(O_O)",
    Expression.RELIEVED: "(^_^)",
    Expression.SATISFIED: "(^‿^)",
    Expression.ATTENTIVE: "(•_•)",
    Expression.WAITING: "(-.-)",
}


def glyph_for(expression: str) -> str:
    """Expressão desconhecida (skew entre backend e este cliente) cai
    pro glifo neutro, nunca quebra o desenho (Seção 57)."""
    try:
        return _GLYPH_BY_EXPRESSION[Expression(expression)]
    except ValueError:
        return NEUTRAL_GLYPH
