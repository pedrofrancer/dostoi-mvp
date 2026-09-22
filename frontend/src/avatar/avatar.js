// Aplica um HumanizedState (vindo do backend) nas partes semânticas do
// SVG. Manipula propriedade, não substitui a imagem inteira (Seção 30).
import { MOUTH_SHAPES } from "./mouth-shapes.js";
import { EXPRESSION_STYLES, resolveExpression } from "./expressions.js";
import { playAnimation } from "./animations.js";

export function applyHumanizedState(root, humanized) {
  const exprName = resolveExpression(humanized.expression);
  const style = EXPRESSION_STYLES[exprName];

  const mouth = root.querySelector("#mouth-path");
  if (mouth) mouth.setAttribute("d", MOUTH_SHAPES[style.mouth]);

  const browLeft = root.querySelector("#eyebrow-left");
  const browRight = root.querySelector("#eyebrow-right");
  if (browLeft) {
    browLeft.style.transform = `translateY(${-style.browLift}px) rotate(${-style.browTilt}deg)`;
  }
  if (browRight) {
    browRight.style.transform = `translateY(${-style.browLift}px) rotate(${style.browTilt}deg)`;
  }

  const eyes = root.querySelector("#eyes");
  if (eyes) eyes.style.transform = `scale(${style.eyeScale})`;

  if (humanized.animation) {
    playAnimation(root, humanized.animation, humanized.duration_ms || 1000);
  }

  root.dataset.expression = exprName;
}
