import {
  WebSocketMessage,
  CodeUpdateMessage,
  PingMessage,
  ConnectionStatus,
} from '../types/analysis';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private readonly url: string;
  private readonly sessionToken: string;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private readonly heartbeatInterval = 30000;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pendingCodeUpdate: string | null = null;
  private sequenceNumber = 0;
  private manualDisconnect = false;

  private readonly onMessage: (message: WebSocketMessage) => void;
  private readonly onStatusChange: (status: ConnectionStatus) => void;
  private readonly onError: (error: string) => void;

  constructor(
    baseUrl: string,
    sessionToken: string,
    onMessage: (message: WebSocketMessage) => void,
    onStatusChange: (status: ConnectionStatus) => void,
    onError: (error: string) => void,
  ) {
    this.url = `${baseUrl.replace(/\\/$/, '')}/ws/code-analysis?session_token=${encodeURIComponent(sessionToken)}`;
    this.sessionToken = sessionToken;
    this.onMessage = onMessage;
    this.onStatusChange = onStatusChange;
    this.onError = onError;
  }

  connect(): void {
    this.manualDisconnect = false;
    this.clearReconnectTimer();

    if (this.ws && [WebSocket.OPEN, WebSocket.CONNECTING].includes(this.ws.readyState)) {
      return;
    }

    this.onStatusChange('connecting');

    try {
      const ws = new WebSocket(this.url);
      this.ws = ws;
      this.setupEventHandlers(ws);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      this.onError(`Connection failed: ${message}`);
      this.onStatusChange('error');
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.manualDisconnect = true;
    this.clearReconnectTimer();
    this.clearHeartbeat();
    this.pendingCodeUpdate = null;

    const ws = this.ws;
    this.ws = null;
    if (ws && ws.readyState !== WebSocket.CLOSED) {
      ws.close(1000, 'Client disconnect');
    }

    this.onStatusChange('disconnected');
  }

  sendCodeUpdate(code: string, language = 'python'): void {
    const message: CodeUpdateMessage = {
      type: 'code_update',
      sequence: ++this.sequenceNumber,
      code,
      language,
      timestamp: Date.now(),
    };
    const serialized = JSON.stringify(message);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(serialized);
    } else {
      // Keep only the newest code snapshot; older queued snapshots are useless.
      this.pendingCodeUpdate = serialized;
    }
  }

  private setupEventHandlers(ws: WebSocket): void {
    ws.onopen = () => {
      if (this.ws !== ws) return;
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.onStatusChange('connected');

      if (this.pendingCodeUpdate) {
        ws.send(this.pendingCodeUpdate);
        this.pendingCodeUpdate = null;
      }

      this.startHeartbeat();
    };

    ws.onmessage = (event) => {
      if (this.ws !== ws) return;

      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        if (message.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
          return;
        }
        this.onMessage(message);
      } catch {
        this.onError('Failed to parse server message');
      }
    };

    ws.onclose = (event) => {
      if (this.ws === ws) this.ws = null;
      this.clearHeartbeat();

      if (this.manualDisconnect || event.code === 1000) {
        this.onStatusChange('disconnected');
        return;
      }

      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.onStatusChange('connecting');
        this.scheduleReconnect();
      } else {
        this.onStatusChange('error');
        this.onError('Connection lost and failed to reconnect');
      }
    };

    ws.onerror = () => {
      if (this.ws !== ws) return;
      this.onError('WebSocket connection error');
    };
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        const ping: PingMessage = { type: 'ping', timestamp: Date.now() };
        this.ws.send(JSON.stringify(ping));
      }
    }, this.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.manualDisconnect || this.reconnectTimer || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    const delay = this.reconnectDelay;
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.manualDisconnect) return;
      this.reconnectAttempts += 1;
      this.connect();
    }, delay);
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get currentStatus(): ConnectionStatus {
    if (!this.ws) return this.manualDisconnect ? 'disconnected' : 'error';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      default:
        return 'disconnected';
    }
  }
}
