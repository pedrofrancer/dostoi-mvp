import { HarnessClient } from "./api.js";
import { applyHumanizedState } from "./avatar/avatar.js";

async function loadAvatarSvg(container) {
  const response = await fetch("avatar.svg");
  container.innerHTML = await response.text();
  return container.querySelector("#avatar");
}

async function main() {
  const container = document.getElementById("avatar-container");
  const statusEl = document.getElementById("connection-status");
  const avatarRoot = await loadAvatarSvg(container);

  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const client = new HarnessClient(`${protocol}//${location.host}/ws`, {
    onConnect: () => {
      statusEl.textContent = "conectado";
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
    },
  });

  client.connect();
}

main();
