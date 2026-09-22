// As dez expressões da Seção 27, cada uma com um tratamento visual
// próprio (boca, inclinação/altura da sobrancelha, escala do olho),
// composto a partir de poucas peças, não um asset por estado.
export const EXPRESSION_STYLES = {
  neutral: { mouth: "flat", browTilt: 0, browLift: 0, eyeScale: 1 },
  focused: { mouth: "flat", browTilt: -4, browLift: -2, eyeScale: 1 },
  curious: { mouth: "flat", browTilt: 6, browLift: 3, eyeScale: 1 },
  thoughtful: { mouth: "flat", browTilt: 8, browLift: 4, eyeScale: 1 },
  concerned: { mouth: "frown", browTilt: -10, browLift: -3, eyeScale: 1 },
  surprised: { mouth: "open", browTilt: 0, browLift: 8, eyeScale: 1.3 },
  relieved: { mouth: "smile", browTilt: 0, browLift: 2, eyeScale: 1 },
  satisfied: { mouth: "smile", browTilt: 0, browLift: 3, eyeScale: 0.9 },
  attentive: { mouth: "flat", browTilt: 2, browLift: 2, eyeScale: 1 },
  waiting: { mouth: "flat", browTilt: 0, browLift: 1, eyeScale: 1 },
};

export const FALLBACK_EXPRESSION = "neutral";

// Seção 57: cair em neutro quando a expressão não existe, nunca quebrar.
export function resolveExpression(name) {
  return Object.prototype.hasOwnProperty.call(EXPRESSION_STYLES, name)
    ? name
    : FALLBACK_EXPRESSION;
}
