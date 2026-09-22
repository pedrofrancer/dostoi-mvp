// Painel de contexto atual (TechSpecs Seção 64): tarefa, agente,
// arquivos tocados, testes, erros recentes.
export function renderContextPanel(container, context) {
  if (!context) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = `
    <div class="context-row"><span>tarefa</span><span>${context.task ?? "—"}</span></div>
    <div class="context-row"><span>agente</span><span>${context.agent}</span></div>
    <div class="context-row"><span>arquivos</span><span>${context.modified_files.length}</span></div>
    <div class="context-row"><span>testes</span><span>${context.tests_passed} ok / ${context.tests_failed} falha</span></div>
    <div class="context-row"><span>erros</span><span>${context.recent_errors.length}</span></div>
  `;
}
