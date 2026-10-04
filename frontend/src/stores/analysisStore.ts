/**
 * Zustand store for real-time code analysis state management
 *
 * Manages WebSocket connection, diagnostics, and analysis metrics
 */

import { create } from 'zustand';
import { WebSocketService } from '../services/websocket';
import {
  Diagnostic,
  WebSocketMessage,
  AnalysisResult,
  ConnectionStatus,
  WebSocketState
} from '../types/analysis';

interface AnalysisStore extends WebSocketState {
  // WebSocket service instance
  wsService: WebSocketService | null;

  // Session info
  connectedAt: number | null;
  serverTime: number | null;

  // Message statistics
  messagesSent: number;
  messagesReceived: number;

  // Internal methods
  _handleMessage: (message: WebSocketMessage) => void;
  _handleStatusChange: (status: ConnectionStatus) => void;
  _handleError: (error: string) => void;
}

const getWebSocketUrl = (): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = (import.meta as any).env?.VITE_WS_URL || `${protocol}//${window.location.host}`;
  return host.replace(/^https?:/, protocol.replace('s', ''));
};

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
  // Connection state
  connectionStatus: 'disconnected',
  sessionToken: null,
  lastError: null,
  wsService: null,

  // Analysis state
  diagnostics: [],
  lastAnalysisTime: null,
  sequenceNumber: 0,

  // Performance metrics
  analysisCount: 0,
  averageAnalysisTime: 0,

  // Session info
  connectedAt: null,
  serverTime: null,

  // Message statistics
  messagesSent: 0,
  messagesReceived: 0,

  // Actions
  connect: (sessionToken = 'default-session') => {
    const state = get();

    // Don't create new connection if already connected with same token
    if (state.wsService && state.sessionToken === sessionToken &&
        state.connectionStatus === 'connected') {
      return;
    }

    // Disconnect existing connection
    if (state.wsService) {
      state.wsService.disconnect();
    }

    const wsUrl = getWebSocketUrl();
    const wsService = new WebSocketService(
      wsUrl,
      sessionToken,
      state._handleMessage,
      state._handleStatusChange,
      state._handleError
    );

    set({
      wsService,
      sessionToken,
      lastError: null,
      sequenceNumber: 0,
      messagesSent: 0,
      messagesReceived: 0,
      connectedAt: null,
      serverTime: null,
    });

    wsService.connect();
  },

  disconnect: () => {
    const { wsService } = get();
    if (wsService) {
      wsService.disconnect();
    }

    set({
      wsService: null,
      connectionStatus: 'disconnected',
      sessionToken: null,
      lastError: null,
      diagnostics: [],
      lastAnalysisTime: null,
      sequenceNumber: 0,
      connectedAt: null,
      serverTime: null,
    });
  },

  sendCodeUpdate: (code: string, language = 'python') => {
    const { wsService, connectionStatus } = get();

    if (!wsService || connectionStatus !== 'connected') {
      console.warn('Cannot send code update: WebSocket not connected');
      return;
    }

    wsService.sendCodeUpdate(code, language);

    set((state) => ({
      messagesSent: state.messagesSent + 1,
    }));
  },

  clearDiagnostics: () => {
    set({
      diagnostics: [],
      lastAnalysisTime: null,
    });
  },

  // Internal message handlers
  _handleMessage: (message: WebSocketMessage) => {
    set((state) => ({
      messagesReceived: state.messagesReceived + 1,
    }));

    switch (message.type) {
      case 'analysis_result':
        const analysisResult = message as AnalysisResult;

        set((state) => {
          // Calculate new average analysis time
          const newCount = state.analysisCount + 1;
          const newAverage = (
            (state.averageAnalysisTime * state.analysisCount + analysisResult.analysis_time_ms) /
            newCount
          );

          return {
            diagnostics: analysisResult.diagnostics,
            lastAnalysisTime: analysisResult.analysis_time_ms,
            analysisCount: newCount,
            averageAnalysisTime: Math.round(newAverage),
            sequenceNumber: Math.max(state.sequenceNumber, analysisResult.sequence),
          };
        });
        break;

      case 'session_info':
        set({
          connectedAt: message.connected_at,
          serverTime: message.server_time,
        });
        break;

      case 'error':
        console.error('WebSocket error:', message.message);
        set({
          lastError: message.message,
        });
        break;

      case 'ping':
      case 'pong':
        // Handled by WebSocket service for heartbeat
        break;

      default:
        console.warn('Unknown message type:', message);
    }
  },

  _handleStatusChange: (status: ConnectionStatus) => {
    set({ connectionStatus: status });

    if (status === 'connected') {
      set({ lastError: null });
    }
  },

  _handleError: (error: string) => {
    set({
      lastError: error,
      connectionStatus: 'error',
    });
    console.error('WebSocket service error:', error);
  },
}));

// Auto-connect on store creation in development
if ((import.meta as any).env?.DEV) {
  // Small delay to ensure component mounting
  setTimeout(() => {
    const store = useAnalysisStore.getState();
    if (store.connectionStatus === 'disconnected') {
      store.connect('dev-session');
    }
  }, 100);
}