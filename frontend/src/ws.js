// WebSocket client for the session manager.
//
// One socket carries everything:
//   - binary messages: H.264 frames ([u8 flags][u64 BE pts_us][Annex B payload])
//   - text messages: JSON control (status, pong, errors, stream_restart, ...)

const HEADER_BYTES = 9;

export class StreamSocket {
  constructor({ onFrame, onJson, onConnectionChange }) {
    this.onFrame = onFrame;
    this.onJson = onJson;
    this.onConnectionChange = onConnectionChange;
    this.ws = null;
    this.closed = false;
    this.retryDelay = 500;
  }

  async connect() {
    this.closed = false;
    let token;
    try {
      const res = await fetch('/api/config');
      token = (await res.json()).token;
    } catch {
      this._scheduleReconnect();
      return;
    }

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/session?token=${token}`);
    ws.binaryType = 'arraybuffer';
    this.ws = ws;

    ws.onopen = () => {
      this.retryDelay = 500;
      this.onConnectionChange('connected');
    };

    ws.onmessage = (ev) => {
      if (typeof ev.data === 'string') {
        try {
          this.onJson(JSON.parse(ev.data));
        } catch {
          /* ignore malformed */
        }
        return;
      }
      const buf = ev.data;
      if (buf.byteLength < HEADER_BYTES) return;
      const view = new DataView(buf);
      const keyframe = (view.getUint8(0) & 1) === 1;
      const ptsUs = Number(view.getBigUint64(1));
      this.onFrame(new Uint8Array(buf, HEADER_BYTES), keyframe, ptsUs);
    };

    ws.onclose = (ev) => {
      this.ws = null;
      // 4409 = another tab owns the session; don't fight over it.
      if (ev.code === 4409) {
        this.onConnectionChange('busy');
        return;
      }
      if (!this.closed) {
        this.onConnectionChange('reconnecting');
        this._scheduleReconnect();
      }
    };

    ws.onerror = () => ws.close();
  }

  _scheduleReconnect() {
    if (this.closed) return;
    setTimeout(() => this.connect(), this.retryDelay);
    this.retryDelay = Math.min(this.retryDelay * 2, 5000);
  }

  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }

  close() {
    this.closed = true;
    this.onConnectionChange('disconnected');
    if (this.ws) this.ws.close();
  }
}
