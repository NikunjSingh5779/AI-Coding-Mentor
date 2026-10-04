/**
 * TypeScript types for real-time code analysis
 */

export interface Diagnostic {
  line: number;
  column: number;
  end_line?: number | null;
  end_column?: number | null;
  message: string;
  severity: 'error' | 'warning' | 'info' | 'hint';
  source: string;
  category: string;
  code?: string | null;
  fix_suggestion?: string | null;
}

export interface AnalysisResult {
  type: 'analysis_result';
  sequence: number;
  session_token: string;
  diagnostics: Diagnostic[];
  analysis_time_ms: number;
  lines_of_code: number;
  has_syntax_errors: boolean;
  performance: {
    within_budget: boolean;
    diagnostic_count: number;
  };
  timestamp: number;
  language: string;
}

export interface CodeUpdateMessage {
  type: 'code_update';
  sequence: number;
  code: string;
  language: string;
  timestamp: number;
}

export interface PingMessage {
  type: 'ping';
  timestamp: number;
}

export interface PongMessage {
  type: 'pong';
  timestamp: number;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
  code: string;
  sequence?: number;
}

export interface SessionInfoMessage {
  type: 'session_info';
  session_token: string;
  connected_at: number;
  server_time: number;
}

export type WebSocketMessage =
  | AnalysisResult
  | PingMessage
  | PongMessage
  | ErrorMessage
  | SessionInfoMessage;

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketState {
  // Connection state
  connectionStatus: ConnectionStatus;
  sessionToken: string | null;
  lastError: string | null;

  // Analysis state
  diagnostics: Diagnostic[];
  lastAnalysisTime: number | null;
  sequenceNumber: number;

  // Performance metrics
  analysisCount: number;
  averageAnalysisTime: number;

  // Actions
  connect: (sessionToken?: string) => void;
  disconnect: () => void;
  sendCodeUpdate: (code: string, language?: string) => void;
  clearDiagnostics: () => void;
}