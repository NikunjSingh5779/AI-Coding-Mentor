/**
 * WebSocket service for real-time code analysis
 *
 * Handles WebSocket connection lifecycle, message queuing, and reconnection logic
 */

import {
  WebSocketMessage,
  CodeUpdateMessage,
  PingMessage,
  ConnectionStatus
} from '../types/analysis';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private sessionToken: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000; // Start with 1 second
  private heartbeatInterval: number = 30000; // 30 seconds
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageQueue: string[] = [];
  private sequenceNumber: number = 0;
  private onMessage: (message: WebSocketMessage) => void;
  private onStatusChange: (status: ConnectionStatus) => void;
  private onError: (error: string) => void;

  constructor(
    baseUrl: string,
    sessionToken: string,
    onMessage: (message: WebSocketMessage) => void,
    onStatusChange: (status: ConnectionStatus) => void,
    onError: (error: string) => void
  ) {
    this.url = `${baseUrl}/ws/code-analysis?session_token=${encodeURIComponent(sessionToken)}`;
    this.sessionToken = sessionToken;
    this.onMessage = onMessage;
    this.onStatusChange = onStatusChange;
    this.onError = onError;
  }

  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    this.onStatusChange('connecting');

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.onError(`Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      this.onStatusChange('error');
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.clearHeartbeat();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.onStatusChange('disconnected');
  }

  sendCodeUpdate(code: string, language: string = 'python'): void {
    const message: CodeUpdateMessage = {
      type: 'code_update',
      sequence: ++this.sequenceNumber,
      code,
      language,
      timestamp: Date.now(),
    };

    this.sendMessage(JSON.stringify(message));
  }

  private sendMessage(message: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      // Queue message for later delivery
      this.messageQueue.push(message);
      console.warn('WebSocket not ready, message queued');
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.onStatusChange('connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000; // Reset delay

      // Send queued messages
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        if (message && this.ws) {
          this.ws.send(message);
        }
      }

      // Start heartbeat
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        // Handle ping/pong
        if (message.type === 'ping') {
          this.sendMessage(JSON.stringify({
            type: 'pong',
            timestamp: Date.now(),
          }));
          return;
        }

        this.onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        this.onError('Failed to parse server message');
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.clearHeartbeat();

      if (event.code === 1000) {
        // Normal closure
        this.onStatusChange('disconnected');
      } else if (this.reconnectAttempts < this.maxReconnectAttempts) {
        // Unexpected closure, attempt reconnect
        this.onStatusChange('connecting');
        this.scheduleReconnect();
      } else {
        // Max reconnection attempts reached
        this.onStatusChange('error');
        this.onError('Connection lost and failed to reconnect');
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.onError('WebSocket connection error');
      this.onStatusChange('error');
    };
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const pingMessage: PingMessage = {
          type: 'ping',
          timestamp: Date.now(),
        };
        this.sendMessage(JSON.stringify(pingMessage));
      }
    }, this.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.onError('Maximum reconnection attempts reached');
      this.onStatusChange('error');
      return;
    }

    setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff with jitter
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2 + Math.random() * 1000,
      30000 // Max 30 seconds
    );
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get currentStatus(): ConnectionStatus {
    if (!this.ws) return 'disconnected';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'error';
    }
  }
}