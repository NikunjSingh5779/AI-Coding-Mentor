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
  WebSocketState,
} from '../types/analysis';

interface AnalysisStore extends WebSocketState {
  wsService: WebSocketService | null;
  connectedAt: number | null;
  serverTime: number | null;
  messagesSent: number;
  messagesReceived: number;
  _handleMessage: (message: WebSocketMessage) => void;
  _handleStatusChange: (status: ConnectionStatus) => void;
  _handleError: (error: string) => void;
}

const getWebSocketUrl = (): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const configured = (import.meta as { env?: { VITE_WS_URL?: string } }).env?.VITE_WS_URL;
  const base = configured || `${protocol}//${window.location.host}`;
  return base.replace(/^https?:/, protocol);
};

const normalizeDiagnostic = (diagnostic: any): Diagnostic => ({
  id: diagnostic.id,
  seq: diagnostic.seq ?? 0,
  line: diagnostic.range?.start?.line ?? diagnostic.line ?? 1,
  column: (diagnostic.range?.start?.column ?? diagnostic.range?.start?.col ?? diagnostic.column ?? 1) - 1,
  end_line: diagnostic.range?.end?.line ?? diagnostic.end_line ?? null,
  end_column:
    (diagnostic.range?.end?.column ?? diagnostic.range?.end?.col ?? diagnostic.end_column ?? null) === null
      ? null
      : (diagnostic.range?.end?.column ?? diagnostic.range?.end?.col ?? diagnostic.end_column) - 1,
  message: diagnostic.message ?? diagnostic.message_raw ?? 'Analysis finding',
  severity: diagnostic.severity,
  source: diagnostic.source ?? diagnostic.origin ?? 'analysis',
  category: diagnostic.category ?? 'unknown',
  code: diagnostic.code ?? diagnostic.rule ?? null,
  fix_suggestion: diagnostic.fix_suggestion ?? null,
  fingerprint: diagnostic.fingerprint,
  confidence: diagnostic.confidence,
});

export const useAnalysisStore = create<AnalysisStore>((set, get) => ({
  connectionStatus: 'disconnected',
  sessionToken: null,
  lastError: null,
  wsService: null,
  diagnostics: [],
  lastAnalysisTime: null,
  sequenceNumber: 0,
  analysisCount: 0,
  averageAnalysisTime: 0,
  connectedAt: null,
  serverTime: null,
  messagesSent: 0,
  messagesReceived: 0,

  connect: (sessionToken = 'default-session') => {
    const state = get();
    if (
      state.wsService &&
      state.sessionToken === sessionToken &&
      state.connectionStatus === 'connected'
    ) {
      return;
    }

    state.wsService?.disconnect();

    let service: WebSocketService;
    const isCurrent = () => get().wsService === service;

    service = new WebSocketService(
      getWebSocketUrl(),
      sessionToken,
      (message) => {
        if (isCurrent()) get()._handleMessage(message);
      },
      (status) => {
        if (isCurrent()) get()._handleStatusChange(status);
      },
      (error) => {
        if (isCurrent()) get()._handleError(error);
      },
    );

    set({
      wsService: service,
      sessionToken,
      lastError: null,
      sequenceNumber: 0,
      messagesSent: 0,
      messagesReceived: 0,
      connectedAt: null,
      serverTime: null,
      diagnostics: [],
      analysisCount: 0,
      averageAnalysisTime: 0,
      lastAnalysisTime: null,
    });

    service.connect();
  },

  disconnect: () => {
    get().wsService?.disconnect();
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
    if (!wsService || connectionStatus !== 'connected') return;
    wsService.sendCodeUpdate(code, language);
    set((state) => ({ messagesSent: state.messagesSent + 1 }));
  },

  clearDiagnostics: () => set({ diagnostics: [], lastAnalysisTime: null }),

  _handleMessage: (message) => {
    set((state) => ({ messagesReceived: state.messagesReceived + 1 }));
    switch (message.type) {
      case 'analysis_result': {
        const result = message as AnalysisResult;
        set((state) => {
          // Drop stale results. The backend also guarantees latest-sequence semantics.
          if (result.sequence < state.sequenceNumber) return state;
          const newCount = state.analysisCount + 1;
          const newAverage =
            (state.averageAnalysisTime * state.analysisCount + result.analysis_time_ms) / newCount;
          return {
            diagnostics: result.diagnostics.map(normalizeDiagnostic),
            lastAnalysisTime: result.analysis_time_ms,
            analysisCount: newCount,
            averageAnalysisTime: Math.round(newAverage),
            sequenceNumber: result.sequence,
          };
        });
        break;
      }
      case 'session_info':
        set({ connectedAt: message.connected_at, serverTime: message.server_time });
        break;
      case 'error':
        set({ lastError: message.message });
        break;
      case 'ping':
      case 'pong':
        break;
    }
  },

  _handleStatusChange: (status) => {
    set({ connectionStatus: status, ...(status === 'connected' ? { lastError: null } : {}) });
  },

  _handleError: (error) => set({ lastError: error, connectionStatus: 'error' }),
}));

