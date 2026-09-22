// Animação genérica por nome de classe CSS (`anim-<nome>`), removida
// sozinha depois de duration_ms. Nome sem CSS correspondente = nenhum
// efeito visual, nunca erro (mesmo espírito de fallback da Seção 57).
export function playAnimation(root, name, durationMs) {
  if (!name) return;
  const className = `anim-${name}`;
  root.classList.remove(className); // reinicia se já estava tocando
  // força reflow pra reiniciar a animação CSS mesmo com o mesmo nome
  void root.offsetWidth;
  root.classList.add(className);
  window.setTimeout(() => root.classList.remove(className), durationMs);
}
