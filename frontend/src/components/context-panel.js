// Painel de contexto atual (TechSpecs Seção 64): tarefa, agente,
// arquivos tocados, testes, erros recentes.
//
// `context.task`/`context.agent` vêm de payload de evento — texto de
// fora do backend, não confiável (Seção 75: nenhuma execução arbitrária
// de fronte). `textContent`, nunca template HTML, pra não abrir XSS
// armazenado via `task_started.description`.
function addRow(container, label, value) {
  const row = document.createElement("div");
  row.className = "context-row";

  const labelSpan = document.createElement("span");
  labelSpan.textContent = label;

  const valueSpan = document.createElement("span");
  valueSpan.textContent = value;

  row.appendChild(labelSpan);
  row.appendChild(valueSpan);
  container.appendChild(row);
}

export function renderContextPanel(container, context) {
  container.innerHTML = "";
  if (!context) {
    return;
  }

  addRow(container, "tarefa", context.task ?? "—");
  addRow(container, "agente", context.agent);
  addRow(container, "arquivos", String(context.modified_files.length));
  addRow(container, "testes", `${context.tests_passed} ok / ${context.tests_failed} falha`);
  addRow(container, "erros", String(context.recent_errors.length));
}
