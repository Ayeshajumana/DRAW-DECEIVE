/**
 * DRAW & DECEIVE - Resilient WebSocket Client
 */

class RoomSocket {
  constructor(roomCode) {
    this.roomCode = roomCode.toUpperCase();
    this.ws = null;
    this.handlers = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 10000;
    this.isExplicitlyClosed = false;
    this.statusListeners = [];
  }

  connect() {
    this.isExplicitlyClosed = false;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/room/${this.roomCode}/`;

    this.notifyStatus('connecting');

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.notifyStatus('connected');
        // Request state recovery on open
        this.send('game.request_state', {});
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const type = payload.type;
          const data = payload.data || {};

          if (this.handlers.has(type)) {
            this.handlers.get(type).forEach((cb) => cb(data));
          }

          // Catch-all listener
          if (this.handlers.has('*')) {
            this.handlers.get('*').forEach((cb) => cb(type, data));
          }
        } catch (err) {
          console.error("Malformed message received:", err, event.data);
        }
      };

      this.ws.onclose = (event) => {
        this.notifyStatus('disconnected');
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (err) => {
        console.warn("WebSocket error:", err);
      };
    } catch (e) {
      console.error("Connection attempt failed:", e);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
    this.notifyStatus('reconnecting', { attempt: this.reconnectAttempts, delay });
    setTimeout(() => {
      if (!this.isExplicitlyClosed) {
        this.connect();
      }
    }, delay);
  }

  send(type, data = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
      return true;
    }
    return false;
  }

  on(eventType, callback) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType).push(callback);
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    if (this.handlers.has(eventType)) {
      const list = this.handlers.get(eventType).filter((cb) => cb !== callback);
      this.handlers.set(eventType, list);
    }
  }

  onStatusChange(callback) {
    this.statusListeners.push(callback);
  }

  notifyStatus(status, details = {}) {
    this.statusListeners.forEach((fn) => fn(status, details));
  }

  close() {
    this.isExplicitlyClosed = true;
    if (this.ws) {
      this.ws.close();
    }
  }
}

window.RoomSocket = RoomSocket;
