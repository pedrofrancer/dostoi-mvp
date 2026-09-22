import { HarnessClient } from "./api.js";
import { applyHumanizedState } from "./avatar/avatar.js";
import { renderTimeline } from "./components/timeline.js";
import { renderContextPanel } from "./components/context-panel.js";

async function loadAvatarSvg(container) {
  const response = await fetch("avatar.svg");
  container.innerHTML = await response.text();
  return container.querySelector("#avatar");
}

async function refreshSessionPanels(sessionId, timelineEl, contextEl) {
  const [timelineRes, sessionRes] = await Promise.all([
    fetch(`/api/sessions/${sessionId}/timeline`),
    fetch(`/api/sessions/${sessionId}`),
  ]);
  if (timelineRes.ok) {
    renderTimeline(timelineEl, await timelineRes.json());
  }
  if (sessionRes.ok) {
    const session = await sessionRes.json();
    renderContextPanel(contextEl, session.context);
  }
}

async function loadMostRecentSessionId() {
  const response = await fetch("/api/sessions");
  if (!response.ok) return null;
  const sessions = await response.json();
  if (sessions.length === 0) return null;
  // sem histórico de "sessão ativa" ainda (isso é persistência, Step
  // 11); a mais recente por started_at é a aproximação razoável agora.
  sessions.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
  return sessions[0].id;
}

async function main() {
  const container = document.getElementById("avatar-container");
  const statusEl = document.getElementById("connection-status");
  const timelineEl = document.getElementById("timeline-container");
  const contextEl = document.getElementById("context-container");
  const avatarRoot = await loadAvatarSvg(container);

  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const client = new HarnessClient(`${protocol}//${location.host}/ws`, {
    onConnect: async () => {
      statusEl.textContent = "conectado";
      // snapshot inicial: sem isso, painel fica vazio até o próximo
      // evento, mesmo que a sessão já tenha histórico.
      const sessionId = await loadMostRecentSessionId();
      if (sessionId) {
        refreshSessionPanels(sessionId, timelineEl, contextEl);
      }
    },
    onDisconnect: () => {
      statusEl.textContent = "desconectado";
    },
    onReconnecting: (delayMs) => {
      statusEl.textContent = `reconectando em ${Math.round(delayMs / 1000)}s...`;
    },
    onMessage: (message) => {
      if (message.type === "state_update") {
        applyHumanizedState(avatarRoot, message.payload.humanization);
      }
      if (message.type === "timeline_update") {
        refreshSessionPanels(message.payload.session_id, timelineEl, contextEl);
      }
    },
  });

  client.connect();
}

main();
