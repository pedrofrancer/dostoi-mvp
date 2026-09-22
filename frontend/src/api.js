// Cliente WebSocket com reconexão exponencial (TechSpecs Seção 58):
// 1s, 2s, 4s, 8s, 16s, teto de 30s.
const BACKOFF_STEPS_MS = [1000, 2000, 4000, 8000, 16000, 30000];

export class HarnessClient {
  constructor(url, handlers = {}) {
    this.url = url;
    this.handlers = handlers;
    this._attempt = 0;
    this._closedByUser = false;
    this._socket = null;
  }

  connect() {
    this._closedByUser = false;
    this._open();
  }

  close() {
    this._closedByUser = true;
    if (this._socket) this._socket.close();
  }

  _open() {
    this._socket = new WebSocket(this.url);

    this._socket.addEventListener("open", () => {
      this._attempt = 0;
      this.handlers.onConnect?.();
    });

    this._socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      this.handlers.onMessage?.(message);
    });

    this._socket.addEventListener("close", () => {
      this.handlers.onDisconnect?.();
      if (!this._closedByUser) this._scheduleReconnect();
    });

    this._socket.addEventListener("error", () => {
      this._socket.close();
    });
  }

  _scheduleReconnect() {
    const delay = BACKOFF_STEPS_MS[Math.min(this._attempt, BACKOFF_STEPS_MS.length - 1)];
    this._attempt += 1;
    this.handlers.onReconnecting?.(delay);
    window.setTimeout(() => {
      if (!this._closedByUser) this._open();
    }, delay);
  }
}
